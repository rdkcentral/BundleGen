JSON Schema files are vocabulary that allows to annotate and validate JSON documents.
In this folder, there are 3 schema files -
1. appMetadataSchema that validates the application metadata JSON available in the OCI image.
2. platformSchema that validates the platform config JSON available in bundlegen/templates/generic/ folder.
3. platform_libsSchema that validates the libraries for the respective platform available in bundlegen/templates/generic/ folder.

In case any of the above schema validation fails, the OCI bundle will not be generated.

---
# Copyright and license
 If not stated otherwise in this file or this component's license file the
 following copyright and licenses apply:

 Copyright 2021 RDK Management

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

 http://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.
