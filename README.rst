=====
pyDHS
=====


The plan is for this to be a generic python-based Distributed Hardware Server project.


Description
===========

The idea is that this code base will provide the necessary functionality to communicate with DCSS and be configurable for different peices of hardware. For example it could be configured to control a Raspberry Pi, or run some python scripts, etc.

To begin with I am thinking about a loop detection DHS so my notes might reflect that bias to begin with.

|  usage might be:
|  ``pyDHS BL-831 loop``  in order to run a loop detection DHS.
|  or
|  ``pyDHS BL-831 deicer``  to run a sample deicer that runs on a Raspberry Pi.


General Framework for a loop DHS
================================
* write in python.
* run on voltron (for access to 8 NVIDIA Titan V GPUs).
* establish port/socket to communicate with DCSS using xos protocol.
* establish port/socket to receive jpeg images from axis video server.
* make periodic RESTful API calls to docker to get loop classification detection information.


DCSS Communications
===================

The beamline uses a distributed control system akin to a hub and spoke control model where the central hub is referred to as DCSS (Distributed Control System Server) and the spokes are called DHSs (Distributed Hardware Controlers). In order to write a new DHS we need to establish communications with DCSS.  

DCSS communicates with DHS using the ``xos`` protocol. All ``xos`` messages are prefixed with a 4 character code that will tell you about the the direction of the message. For example:  

| ``stoc_`` **s**\ erver **to** **c**\ lient for messages originating from DCSS and destined for a client application.  
| ``stoh_`` **s**\ erver **to** **h**\ ardware for messages originating from DCSS and destined for hardware (i.e. a DHS).  
| ``htos_`` **h**\ ardweare **to** **s**\ erver for messages originating from a DHS and destined for DCSS.  
| ``gtos_`` **G**\ UI **to** **s**\ erver for messages originating from the Blu-Ice GUI and destined for DCSS.  
| ``stog_`` **s**\ erver **to** **G**\ UI for messages originating from DCSS and destined for the Blu-Ice GUI.  

``xos`` messages come in 2 flavors:  

1. ``xos1`` messages are always 200 bytes in length.  
2. ``xos2`` messages can be up to 1024 bytes, but the first message from DCSS to the DHS and the first response from the DHS back to DCSS must be exactly 200 bytes ONLY.  

connecting to DCSS
------------------

Open a socket to the dcss server on port 14242  
You will receive a 200 byte message:  

``stoc_send_client_type\0\0\0\0\0\0\0\0\0...``

Read 200 bytes from the socket.  
The trailing end of the string ("...") can be garbage, but is usually zeroes.  

Respond with:  

``htos_client_is_hardware loopDHS\0\0\0...``

The very first response must be padded to 200 bytes. Need at least one zero at the end of the meanigful text.  

DCSS will then send messages about the different motors, shutters, ion guages, and operations that it thinks this DHS is responsible for:  

|  ``stoh_register_operation operationName1 operationName1\0\0\0...``  
|  ``stoh_register_operation operationName2 operationName2\0\0\0...``  
|  ``stoh_register_operation operationName3 operationName3\0\0\0...``  

no need to respond to ``stoh_register_operation`` messages.

motor example needed
shutter example needed


pyDHS should then start to listen for messages from DCSS.
---------------------------------------------------------

These are the two important ones for a DHS that is performing operations only.  

|  ``stoh_start_operation``  
|  ``stoh_abort_all``  

if controlling motors or shutter then need examples here.


The ``stoh_start_operation`` messages look like this  
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

``stoh_start_operation operationName1 operationID arg1 arg2 .... argN``  

|  ``operationName1``   the operation that DCSS has requested this DHS to execute.  
|  ``operationID``   a unique numeric ID used to keep track of this operation instance.  
|  ``arg1 arg2 .... argN``   optional set of args to pass into the DHS from DCSS.  

pyDHS should respond with periodic updates in the form of  
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

``htos_operation_update operationName1 operationID updateMessage``  


| ``operationName1``   the operation that DCSS has requested this DHS to execute.  
| ``operationID``   a unique numeric ID used to keep track of this operation instance.  
| ``updateNessage``   anything you want to pass back to DCSS.  

and when the operation is completed with a message like this  
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

``htos_operation_completed operationName1 operationID reason returnMessage``  

| ``operationName1``   the operation that DCSS has requested this DHS to execute.  
| ``operationID``   a unique numeric ID used to keep track of this operation instance.  
| ``reason``   in theory can be anything, but normally would be `normal` or `error`
| ``updateMessage``   any addition you want to pass back to DCSS.  

It is also worth noting that DCSS can "go away" and it is important that the DHS be able to automagically re-establish the socket connection should this happen.

AXIS Video Receiver Port  
==========================

will need to open a port than can receive a stream of jpeg images from our axis video server. The AutoML API requires that images be base64 encoded.

RESTful API loop detection and classification  
===============================================

details of the Google Cloud AutoML docker stuff will go here.  

These are all the operations the current camera DHS is responsible for  
========================================================================

.. code-block:: sh

   initializeCamera  
   getLoopTip  
   getPinDiameters
   addImageToList
   findBoundingBox
   getVerticalCut
   getLoopInfo
   collectLoopImages
   stopCollectLoopImages
   reboxLoopImage


we may not need/want all of these in new loopDHS



psuedo code for a loop DHS
==========================

`loopFast.tcl` or similar scripted operation running in the dcss tcl interpreter performs the following:  

.. code-block:: sh

   dcss/loopFast sends collectLoopImages to loopDHS (stoh_start_operation )  
      loopDHS starts listening for jpg images via http socket from axis server  
   dcss/loopFast start the gonio moving via a `start_oscillation gonio_phi video_trigger $osci_delta $osci_time`  
      loopDHS is receiving the jpegs and storing them somehow.  
   dcss/loopFast sends stopCollectLoopImages  
      loopDHS sends images to docker for loop classification and detection.  
      loopDHS does some minimal set of calculation from the bbox data received from docker.  
      loopDHS returns a list of list. we can discuss exactly what gets passed back.  


There is a 1024 byte limit to each ``xos2`` response so we will probably have to break this down and send the results from each image back to DCSS one at a time, and then reassemble within the ``loopFast.tcl`` scripted operation.

.. code-block:: tcl

   [
   [image_num, tipX, tipY, bboxMinX, bboxMaxX, bboxMinY, bboxMaxY, loop_width, loop_type],
   [image_num, tipX, tipY, bboxMinX, bboxMaxX, bboxMinY, bboxMaxY, loop_width, loop_type],
   .
   .
   .
   [image_num, tipX, tipY, bboxMinX, bboxMaxX, bbpxMinY, bboxMaxY, loop_width, loop_type],
   ]


Note
====

This project has been set up using PyScaffold 3.2.3. For details and usage
information on PyScaffold see https://pyscaffold.org/.
