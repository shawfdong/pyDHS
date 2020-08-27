=====
pyDHS
=====


The plan is for this to be a generic python-based Distributed Hardware Server project.


Description
===========

This code base will provide the necessary functionality to communicate with DCSS and be configurable for different peices of hardware. For example it could be configured to control a Raspberry Pi, or run some python scripts, etc.

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

The beamline uses a distributed control system akin to a hub and spoke control model where the central hub is referred to as DCSS (Distributed Control System Server) and the spokes are called DHSs (Distributed Hardware Controllers). In order to write a new DHS we need to establish communications with DCSS.  

DCSS communicates with DHS using the ``xos`` protocol. All ``xos`` messages are prefixed with a 4 character code that will tell you about the the direction of the message. For example:  

| ``stoc_`` **s**\ erver **to** **c**\ lient for messages originating from DCSS and destined for a client (hardware or software).  
| ``stoh_`` **s**\ erver **to** **h**\ ardware for messages originating from DCSS and destined for hardware (i.e. a DHS).  
| ``htos_`` **h**\ ardweare **to** **s**\ erver for messages originating from a DHS and destined for DCSS.  
| ``gtos_`` **G**\ UI **to** **s**\ erver for messages originating from the Blu-Ice GUI and destined for DCSS.  
| ``stog_`` **s**\ erver **to** **G**\ UI for messages originating from DCSS and destined for the Blu-Ice GUI.  

Details can be found in the `DCS Admin Guide <https://github.com/dsclassen/pyDHS/blob/master/docs/DCSS_ADMIN_GUIDE.pdf>`. This PDF documentation is quite old at this point and has not been updated since 2005, but ti is still worth browsing if you intend to write a functioning DHS.

....

xos
===

The messaging protol used with DCSS/DHS/Blu-Ice control system.

``xos`` messages come in 2 flavors:  

1. ``xos1`` messages are always 200 bytes in length.  
2. ``xos2`` messages can be up to 1024 bytes, but the first message from DCSS to the DHS and the first response from the DHS back to DCSS must be exactly 200 bytes ONLY.  

....

Connect to DCSS
---------------------------------------------------------

Open a socket to the dcss server on port 14242  
You will receive a 200 byte message:  

``stoc_send_client_type\0\0\0\0\0\0\0\0\0...``

Read 200 bytes from the socket.  
The trailing end of the string ("...") can be garbage, but is usually zeroes.  

Respond with:  

``htos_client_is_hardware loopDHS\0\0\0...``

The very first response must be padded to 200 bytes. Need at least one zero at the end of the meanigful text.  

DCSS will then send messages about the different motors, shutters, ion guages, strings, and operations that it thinks this DHS is responsible for:  

|  ``stoh_register_operation operationName1 operationName1\0\0\0...``  
|  ``stoh_register_operation operationName2 operationName2\0\0\0...``  
|  ``stoh_register_operation operationName3 operationName3\0\0\0...``  

|  ``stoh_register_real_motor motor1 motor1\0\0\0...``  
|  ``stoh_register_real_motor motor2 motor2\0\0\0...``  

|  ``stoh_register_string string1 standardString\0\0\0...``  
|  ``stoh_register_string string2 string2\0\0\0...``  

It is also worth noting that DCSS can "go away" and it is important that the DHS be able to automagically re-establish the socket connection should this happen.

....

Configure motors, shutters, strings, ion gauges, and operations
---------------------------------------------------------------

Configure motors by sending an ``htos_configure_device`` command. For example:  

``htos_configure_device energy 12398.42 20000 2000 1 100000 1 -600 0 0 1 0 0 0\0...``  

Where:

======    ==============================    ===============================================================
field     value                             notes
======    ==============================    ===============================================================
1         |  ``htos_configure_device``      The xos command to configure a device.
2         |  ``energy``                     The name of the motor you are configuring.
3         |  ``12398.42``                   The current position of this motor.
4         |  ``20000``                      The forward limit (in motor base units)
5         |  ``2000``                       The reverse limit (in motor base units)
6         |  ``1``                          The motor scale factor (steps/unit)
7         |  ``100000``                     The maximum speed (steps/sec)
8         |  ``1``                          The maximum acceleration (milliseconds)
9         |  ``-600``                       The backlash magnitude and direction (steps).
10        |  ``0``                          Enable the forward limit.  "1" is enabled "0" is disabled.
11        |  ``0``                          Enable the reverse limit.  "1" is enabled "0" is disabled.
12        |  ``0``                          Lock the motor.  "1" is locked "0" unlocked
13        |  ``0``                          Enable anti-backlash movement.  "1" enabled "0" disabled
14        |  ``0``                          Reverse the motor direction.  "1" enabled "0" disabled
15        |  ``0``                          Circle mode. (might be used for gonio phi?)
======    ==============================    ===============================================================


You must pad the message up to 200 bytes and use a zero byte to end the meaningful string.
If you enable the limits (fields 10 & 11), then DCSS will not ask you to move this motor beyond the numbers listed in fields 4 & 5.

Configure shutters by sending an ``htos_configure_shutter`` command. For example:  

|  ``htos_configure_shutter shutter open close open\0...``  
|  or  
|  ``htos_configure_shutter Se open close open\0...``  

Where:

======    ==============================    ===============================================================
field     value                             notes
======    ==============================    ===============================================================
1         |  ``htos_configure_shutter``     | The xos command to configure a shutter.  
2         |  ``shutter``                    | The name of the shutter you are configuring.  
3         |  ``open``                       | The name for the "open" position of this shutter.  
4         |  ``closed``                     | The name for the "closed" position of this shutter.  
5         |  ``open``                       | The current position of this shutter.  
======    ==============================    ===============================================================

Although you can get a away with using "in" and "out" or "on" and "off" for shutter devices, there are certain situations in DCSS where this doesn’t work, so just use "open" and "closed" for everything.  NOTE: it is "closed" and **NOT** "close".

Configure strings by sending an ``htos_set_string_completed`` command. For example:  

|  a simple string with a single word
|  ``htos_set_string_completed detectorType normal PILATUS6``  
|  or a string with multiple key/value pairs
|  ``htos_set_string_completed detectorStatus normal TEMP 26.0 HUMIDITY 2.1 GAPFILL -1 EXPOSUREMODE null DISK_SIZE_KB 0 DISK_USED_KB 0 DISK_USE_PERCENT 0 FREE_IMAGE_SPACE 0 SUM_IMAGES false SUM_IMAGES_DELTA_DEG 0.1 N_FRAME_IMG 1 THRESHOLD 6330.0 GAIN autog THRESHOLD_SET false SETTING_THRESHOLD false``  

Where:  

======    ================================    ===============================================================
field     value                               notes
======    ================================    ===============================================================
1         |  ``htos_set_string_completed``    | The xos command to set a string in DCSS.  
2         |  ``detectorType``                 | The name of the string you are configuring.  
3         |  ``normal``                       | Tell DCSS that the string value was set.  
4         |  ``string1``                      | The value of the string.  
5         |  ``more values``                  | More values (optional).  
======    ================================    ===============================================================


Strings are denoted as ``standardString`` or as mirror of teh stringname. I'm entirely clear on the importance or significance of this difference.

....

Listen for messages from DCSS.
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


....

AXIS Video Receiver Port  
==========================

will need to open a port than can receive a stream of jpeg images from our axis video server. The AutoML API requires that images be base64 encoded.

....

RESTful API loop detection and classification  
===============================================

details of the Google Cloud AutoML docker stuff will go here.  

....

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

....

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

....

Note
====

This project has been set up using PyScaffold 3.2.3. For details and usage
information on PyScaffold see https://pyscaffold.org/.
