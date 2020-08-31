#
# a test DHS. 
#

   class testDHS(dcss.Server):
      testDHSVar = "12345"

      def some_dhs_operation(self, operation, *args):
         try:
            do_things()
         except Exception as error:
            operation.operation_error(str(error))
         else:
            operation.operation_completed('things were done')
