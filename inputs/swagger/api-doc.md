create_library_documentation = """
Path = /library/rest/add/
Function Description:
* This API creates a new Library Image (Machine) with the provided hardware configuration.

Function Parameters:
* Request Body:
    - name (string, required): Library name. Must not contain '/' or '#'.
    - description (string, optional): Description of the library.
    - is_public (boolean, optional, default: false): Only Admin or Restricted group manager can create public images.
    - localize_on_primary (boolean, optional, default: false): Only meaningful for public images.
    - hw (object, required): Hardware configuration.
        - arch (string, optional, default: "x86_64"): One of "x86_64", "aarch64".
        - cpus (integer, optional, default: 4): Minimum 1.
        - ram (integer, optional, default: 1024): Minimum 100.
        - boot (string, optional, default: "hd"): One of "hd", "cdrom", "network".
        - console (string, optional, default: "vnc"): One of "vnc", "spice".
        - hw_version (string, optional): Hardware version string.
        - is_x64 (boolean, optional, default: false): Indicates 64-bit mode.
        - is_uefi (boolean, optional, default: false): Must be true for "aarch64".
        - nvram (object, optional): Used only when is_uefi is true.
            - template (string, optional): NVRAM template path. Defaults to secure template for x86_64; defaults to AAVMF template for aarch64.
        - disks (array, required key): Disk list. Provide this key even if empty (`[]`).
            - port (string, required): IDE ports hda-hdd, SATA sda-sdz, VIRTIO vda-vdz.
            - type (string, required): "ide", "sata", "virtio".
            - size (integer, optional, default: 20): Disk size in GB (minimum 1).
            - format (string, optional, default: "qcow2"): Only "qcow2" is supported.
            - is_boot (boolean, optional, default: false)
            - boot_order (integer, required if is_boot is true): Must be unique across bootable disks.
        - cdrom (array, optional but must be present): Provide `[]` when no CD-ROMs are needed.
            - type (string, required): "ide", "sata", "virtio" (ARM requires "virtio").
            - iso (string, optional)
            - is_boot (boolean, optional, default: false)
            - boot_order (integer, required if is_boot is true): Must be unique across bootable cdroms.
        - networks (array, optional but must be present): Provide `[]` when no NICs are needed.
            - mac (string, optional): Use "auto" or omit to auto-generate; otherwise must match "AA:BB:CC:DD:EE:FF".
            - type (string, optional): "bridge" or "host".
            - model (string, required): "virtio", "e1000", "rtl8139" (ARM requires "virtio").
            - segment (object, optional):
                - If type is "bridge", segment must be "Default Public Segment".
                - If type is "host", segment must be "HostOnly Segment".
            - is_connected (boolean, optional, default: true)
        - serialports (array, optional but must be present): Provide `[]` when no serial ports are needed.
            - source_type (string, optional, default: "pty")
            - target_type (string, optional, default: "isa-serial") (max 3 isa-serial ports total)
            - source_path (string, optional)
            - tcp_ip (string, optional)
            - tcp_port (integer, optional)
            - socket_mode (string, optional): "bind" or "connect"
            - use_telnet (boolean, optional, default: false)
    - Note: hvm_type is not accepted in the request; hypervisor is always KVM.
    - Note: Fields like revision, ctime, owner, state, compliance_state, tags, sw, cloned_from, consolidated_from are read-only and not applied on create.

Returns:
* Response:
    * (Status 201): Library successfully created. Response body is the full Library object.
        - Library UUID is returned in the `uuid` field.
    * (Status 400): Invalid request data or hardware validation errors.
    * (Status 401): Unauthorized, user not logged in.
    * (Status 403): Forbidden (e.g., trying to create a public image without required privileges).

Raises:
* Exception: Any unexpected exceptions.
* ValidationError:
    - Invalid input format.
"""

obtain_auth_token_documentation = """
Path = /auth/
Function Description:
* This API is used to obtain an authentication token for a user.

Function Parameters:
* request_body:
    - username (required): The username of the user requesting the token.
    - password (required): The password of the user requesting the token.
    - key_name (optional): The name of the key associated with the user for token generation.

Returns:
* Response:
    * (Status 200): Token obtained successfully.
    * (Status 401): Unauthorized, Invalid username or password..
Raises:
* Exception: Any unexpected exceptions.
"""

deploy_documentation = """
Path = /deploy/rest/deploy/{uuid}/
Function Description:
* This API deploys a new instance of a machine.

Function Parameters:
* URL Parameter:
    - uuid (string, required): The unique identifier of the machine to be deployed.

* Request Body:
    - count (integer, optional): Number of instances to deploy.
    - sync (boolean, optional): Whether the deployment should be synchronous.
    - vnc_password (string, optional): VNC password for the deployed machine.
    - name (string, optional): Name of the deployed machine (cannot contain `/`).
    - server_list (array of strings, optional): List of server hostnames.
    - group_list (array of strings, optional): List of group names.
    - mac_list (array of strings, optional): List of MAC addresses.
    - tag_list (array of strings, optional): List of tags for the deployment.
    - deploy_start (boolean, optional): Whether to start the deployment immediately (default is 'False').
    - reserve_data_disk (boolean, optional): Whether to reserve the data disk.
    - timetolive (integer, optional): Time-to-live value for the deployment(in Seconds).

Returns:
* Response:
    * (Status 200): Machine deployed successfully.
        - Single deploy (count = 1): Response is a DeployedMachine object with keys such as:
            - uuid: Deployment UUID (this is the deployed instance ID).
            - name, state, description, server, owner, console_port.
            - created_on, utime, deployed_time, timetolive, job_uuid.
            - machine: Nested machine/library info for the deployed instance.
            - source_image_uuid: UUID of the source Library Image used to deploy.
            - tags, protected, compliance_state, deprecation_mode.
            - Autostart settings fields (added by serializer).
        - Bulk deploy (count > 1): Response is an object:
            - bulk_job_uuid: Monitoring task UUID for the bulk deploy (can be null).
            - deployments: List of DeployedMachine objects (same shape as single deploy).
    * (Status 400): Invalid parameters provided or Server in Offline or Maintenance state.
    * (Status 401): Unauthorized, user not logged in.
    * (Status 403): Forbidden, User does not have permission to deploy.
    * (Status 404): Machine UUID not found.


rtask_details_api_documentation = """
Path = /rtask/rest/detail/{uuid}/
Function Description:
* This API retrieves detailed information about a remote task, identified by its UUID.

Function Parameters:
* URL Parameter:
    - uuid (string, required): The unique identifier of the remote task whose details are to be fetched.

Returns:
* Response:
    * (Status 200): A RemoteTask detail object. Response fields include:
        - uuid: Task UUID.
        - id: Numeric task ID.
        - type, type_name: Task type code and human-readable name.
        - status, status_name: Task status code and human-readable name.
            - Status codes:
                - 1: Created
                - 2: Delegated
                - 3: Started
                - 4: Finished
                - 5: Failed
                - 6: Cancel (cancel requested)
                - 7: Cancelling
                - 8: Cancelled
            - Polling guidance:
                - Ongoing statuses: 1, 2, 3, 6, 7 (Created, Delegated, Started, Cancel, Cancelling).
                - Terminal statuses: 4, 5, 8 (Finished, Failed, Cancelled).
        - task_for_name: Server hostname (resolved from task_for).
        - task_on_name: Target object name/hostname (resolved from task_on).
        - percentage: Progress percentage (if available).
        - try_count: Retry count.
        - pid: Remote PID (if available).
        - result: Parsed result dictionary (may be empty).
        - mtime: Last modified timestamp.
        - monitor_for: Monitor task label (if present in extra).
        - failed_childs_uuids, finished_childs_uuids, cancelled_childs_uuids: Lists for child task states (empty if not a parent task).
        - object_type: Target object type inferred from task_on (empty if unknown).
        - For Admin/Restricted Manager only: owner_name, task_for, task_on, extra.
    * (Status 401): Unauthorized - User is not authenticated.
    * (Status 404): Task not found for the provided UUID.

Raises:
* Exception: Any unexpected exceptions.
* ValidationError: If no task exists for the given UUID.
"""

deployed_machine_snapshot_documentation = """
Function Description:
* This API triggers a snapshot operation for the specified deployment UUID of a machine.

Function Parameters:
* URL Parameter:
    - uuid: The unique identifier of the deployed machine.
* Request Body:
    - description: A description to be associated with the snapshot (Optional).

Returns:
* Response:
    * (Status 201): Snapshot task created successfully. Response body is a task descriptor:
        - err: false
        - uuid: Deployment UUID (same as request path uuid)
        - name: Deployment name
        - state: Current deployment state (string)
        - operation: "snapshot"
        - task_uuid: RemoteTask UUID to poll for completion
        - snapshotted_machine_uuid: UUID of the newly created library revision (if created)
    * (Status 400): Validation or state errors, for example:
        - Description exceeds 255 characters
        - Disk UUIDs not part of the machine
        - Snapshot operation not allowed for current state
    * (Status 401): Unauthorized - User is not logged in.
    * (Status 403): Forbidden - User is not the owner, lacks manager rights or admin rights.
    * (Status 404): Machine with the specified UUID was not found.

Raises:
* Exception: For any unexpected errors.
* ValidationError:
    - The specified machine UUID does not exist.
"""


deploy_delete_machine_documentation = """
HTTP Method = Delete
Path = /deploy/rest/delete/{uuid}/
Function Description:
* This API allows deleting a deployed machine by its UUID. Optionally, it can delete the corresponding source library image as well if specified.

Function Parameters:
* Request Body:
    - lib_delete (boolean, optional, default: false): If true, deletes the deployment and its source library image.
    - force (boolean, optional, default: false): If true, forces delete irrespective of current state.
Returns:
* Response:
    * (Status 201): Delete task created successfully. Response body is a task descriptor:
        - err: false
        - uuid: Deployment UUID (same as request path uuid)
        - name: Deployment name
        - state: Current deployment state (string)
        - operation: "delete"
        - task_uuid: RemoteTask UUID to poll for completion
    * (Status 400): Delete task could not be created, for example:
        - Deployment is part of an Island
        - Deployment is protected
    * (Status 401): Unauthorized, if no user is logged in.
    * (Status 403): Forbidden, User is not Owner or doesn't have manager rights over the machine or has Admin rights.

Raises:
* Exception: Any unexpected exceptions.
* ValidationError:
    - Machine with the specified UUID does not exist.
"""


library_delete_documentation = """
Path = /library/rest/delete/{uuid}/
HTTP Method = Delete
Function Description:
* This API deletes a Library Image based on the provided `uuid`.

Function Parameters:
* Path Parameters:
    - uuid: The unique identifier of the Library Image to be deleted.
* request_body:
    - full_tree: A boolean value to determine wether to delete all the revisions of the passed UUID of Library Image. It will delete all the previous Library images beneath this revision.


Returns:
* Response:
    * (Status 204): No Content, the Image has been successfully deleted.
    * (Status 400): Any unexpected Exception / ValidationError
    * (Status 401): Unauthorized, user not logged in.
    * (Status 403): Forbidden, If User is not Owner/Admin or has manager privelleges over the Image.
    * (Status 404): Image with provided uuid not found.

Raises:
* Exception: Any unexpected exceptions.
* ValidationError:
    - Image with the specified UUID does not exist.
"""

get_server_list_api_documentation = """
HTTP Method = GET
Path = /servers/rest/list/
Function Description:
* This API allows authenticated users to retrieve a list of servers.
* It supports advanced filtering, searching, ordering, and pagination.

Function Parameters:
* URL Parameters:
    - uuid (string, optional): Filter by server UUID.
    - total_disk (number, optional): Filter by the server's total disk size.
    - total_ram (number, optional): Filter by the server's total RAM size.
    - group_id (string, optional): Filter servers that belong to a specific group (by ID or name).
    - exclude_group_id (string, optional): Exclude servers from a specific group.
    - hostname (string, optional): Case-insensitive partial match for server hostname.
    - status (string, optional): Comma-separated list of server statuses or installation stages to filter by[Excludes 'Installed' stage.].
    - disk_health (string, optional): Comma-separated list of disk health values to filter by.
        * Accepted values include: Healthy, Warning, Critical.
        * Internally maps to disk usage percentage thresholds.
    - ip (string, optional): Case-insensitive partial match for server IP address.
    - replicating_db (string, optional): Filter based on whether the server is replicating the database.
        * Values: "true" or "false"
    - arch (string, optional): Filter by system architecture. Case-insensitive exact match.
    - scope (string, optional): Scope of server access. [Choices:"my", "all", "public"]
    - search (string, optional): Case-insensitive search across multiple fields.
        * Searches across: hostname, total_disk, total_ram, ip, hvm_type, arch.
    - ordering (string, optional): Field to order results by. Prefix with "-" for descending order.
        * Valid fields: ip, hostname, hvm_type, used_disk, used_ram, arch.
    - page (integer, optional): Page number for paginated result.
    - page_size (integer, optional): Number of results per page.

Returns:
* Response:
    * (Status 200): Returns a paginated list of server objects in JSON format.
    * (Status 401): Unauthorized - User is not authenticated.
    * (Status 404): Not Found - The requested page does not exist.
        - This may occur if the page number is invalid (e.g., negative, zero, or beyond the total number of pages).

Raises:
* Exception: Any unexpected exceptions.
"""

server_bulkops_documentation = """
Path = /servers/rest/bulkops/
HTTP Method = POST
Function Description:
* This API performs bulk operations on servers.

Function Parameters:
* Request Body:
    * op (required): A String that specifies the type of operation to perform.
                            All these operations are case-sensitive and must be provided in lowercase letters. For example:
        - `syncrepo`: Starts Syncrepo (Localizing Public Image Layers and Nvrams) operation of provided Server.
        - `delete`: Deleting the provided server.
        - `upgrade`: Upgrades the provided server which should be a Managed Host.
        - `lock_server`: Changes the state of server to Locked.
        - `unlock_server`: Unlocks the server which is in Locked state.
        - `mark_for_maintenance`: Changes the state of server to  Maintenance.
        - `unmark_for_maintenance`: Unmarks the server which is in Maintenance state.

    - server_list (array of strings, required): A list of server uuids.
    - credentials(optional): Username and Password (Only required for Upgrade operation)

Returns:
* Response:
    * (Status 202): Operation completed successfully.
    * (Status 207): Either all or some operations failed
    * (Status 400):
        - Invalid input data or missing required fields.
        - Any unexpected Exception.
    * (Status 401): Unauthorized, user not logged in.

Raises:
* Exception: Any unexpected exceptions.
* ValidationError:
    - Server List is Empty
    - Provided Servers are not in List datatype
    - Unsupported Operation
"""

library_list_documentation = """
Path = /library/rest/viewmachinelist/
HTTP Method = GET
Function Description:
* This API retrieves a list of libraries based on various filters and query parameters.

Function Parameters:
* URL Parameter:
    - uuid (string, optional): Filters libraries whose UUID contains the given string.
    - name (string, optional): Filters libraries whose name contains the given string.
    - description (string, optional): Filters libraries whose description contains the given string.
    - cpus (integer, optional): Filters libraries with the exact CPU count.
    - ram (integer, optional): Filters libraries with the exact RAM size.
    - ram_min (integer, optional): Filters libraries with at least the specified RAM size.
    - ram_max (integer, optional): Filters libraries with at most the specified RAM size.
    - hvm_type (string, optional): Filters libraries based on their HVM type.
    - arch (string, optional): Filters libraries based on their architecture.
    - boot (string, optional): Filters libraries based on their boot options.
    - console (string, optional): Filters libraries based on their console type.
    - hw_version (string, optional): Filters libraries based on their hardware version.
    - is64 (boolean, optional): Filters libraries based on 64-bit architecture.
    - is_uefi (boolean, optional): Filters libraries that support UEFI.
    - owner (string, optional): Filters libraries based on owner username.
    - disk_size (integer, optional): Filters libraries based on disk size.
    - nvram_size (integer, optional): Filters libraries based on NVRAM size.
    - nvram_uuid (string, optional): Filters libraries based on NVRAM UUID.
    - disk_size_min (integer, optional): Filters libraries with at least the specified disk size.
    - disk_size_max (integer, optional): Filters libraries with at most the specified disk size.
    - disk_uuid (string, optional): Filters libraries based on disk UUID.
    - mac (string, optional): Filters libraries based on MAC address.
    - iso (string, optional): Filters libraries based on attached ISO image.
    - created_start_date (datetime, optional): Filters libraries created after the specified date.
    - created_end_date (datetime, optional): Filters libraries created before the specified date.
    - created_date_range (string, optional): Filters libraries within a time range. Options: 'today', 'yesterday', 'week', 'month', 'year'.
    - _sessionid (string, optional): Filters libraries based on session ID.
    - _session_name (string, optional): Filters libraries based on session name.
    - _session_created_on (datetime, optional): Filters libraries based on session creation date.
    - tags (string, optional): Filters libraries based on associated tags.
    - revision (integer, optional): Filters libraries based on revision number.
    - compliance_state (string, optional): Filters libraries based on compliance status.
    - search (string, optional): A search term to filter the results.
    - ordering (string, optional): Field to use when ordering the results. Options: 'name', 'hw__ram', 'ctime', 'sw__os'.
    - page (integer, optional): A page number within the paginated result set.
    - page_size (integer, optional): Number of results to return per page.
    - scope (string, optional): Defines the visibility scope. Options: 'all', 'my', 'public'.
    - fetch_all_revs (boolean, optional): If 'true', returns all Libraries of any revision matching the filter.
    - protected (boolean, optional): If 'true', returns all those Libraries that are marked protected.

Returns:
* Response:
    * (Status 200): List of libraries successfully retrieved.
    * (Status 400): Invalid request parameters.
    * (Status 401): Unauthorized - User is not authenticated.

Raises:
* Exception: Any unexpected errors.
* ValidationError:
    - If an invalid query parameter is provided.
"""
