# Copyright 2001, 2002, 2003 by Fle3 Team and contributors

import FLE

def initialize(context):
    """Initialize FLE product."""
    context.registerClass(
        FLE.FLE,
	meta_type='Fle3 %s' % FLE.FLE_VERSION,
        constructors = (FLE.manage_addFLEForm,
                        FLE.manage_addFLE),
        icon='ui/images/fle_logo2.gif'
        )

# EOF
