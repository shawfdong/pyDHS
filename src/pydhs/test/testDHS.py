#
# a test DHS. 
#

# from pydhs.dcss.server import Server
class testDHS(object):
   def __init__(self, dhs, ip):
      self.dhs = dhs
      self.ip = ip

   testDHSVar = "12345"
   '''
   def some_dhs_operation(self, operation, *args):
      try:
         do_things()
      except Exception as error:
         operation.operation_error(str(error))
      else:
         operation.operation_completed('things were done')
   '''