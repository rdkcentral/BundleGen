#!/bin/sh

##############################################################################
# Copyright © 2021 Liberty Global B.V. and its Licensors.
# All rights reserved.
# Licensed by RDK Management, LLC under the terms of the RDK license.
# ============================================================================
# Liberty Global B.V. CONFIDENTIAL AND PROPRIETARY
# ============================================================================
# This file (and its contents) are the intellectual property of Liberty Global B.V.
# It may not be used, copied, distributed or otherwise disclosed in whole or in
# part without the express written permission of Liberty Global B.V.
# The RDK License agreement constitutes express written consent by Liberty Global.
# ============================================================================
# This software is the confidential and proprietary information of Liberty Global B.V.
# ("Confidential Information"). You shall not disclose this source code or
# such Confidential Information and shall use it only in accordance with the
# terms of the license agreement you entered into.
#
# LIBERTY GLOBAL B.V. MAKES NO REPRESENTATIONS OR WARRANTIES ABOUT THE
# SUITABILITY OF THE SOFTWARE, EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT
# LIMITED TO THE IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
# PARTICULAR PURPOSE, OR NON-INFRINGEMENT. LIBERTY GLOBAL B.V. SHALL NOT BE LIABLE FOR
# ANY DAMAGES SUFFERED BY LICENSEE NOR SHALL THEY BE RESPONSIBLE AS A RESULT
# OF USING, MODIFYING OR DISTRIBUTING THIS SOFTWARE OR ITS DERIVATIVES.
##############################################################################

TARGET="7218c" TARGET_VERSION="dunfell" MATCH_MODE="normal" ./test/build_and_test.sh "$@"
