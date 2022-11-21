JSON Schema files are vocabulary that allows to annotate and validate JSON documents.
In this folder, there are 3 schema files -
1. appMetadataSchema that validates the application metadata JSON available in the OCI image.
2. platformSchema that validates the platform config JSON available in bundlegen/templates/generic/ folder.
3. platform_libsSchema that validates the libraries for the respective platform available in bundlegen/templates/generic/ folder.

In case any of the above schema validation fails, the OCI bundle will not be generated.