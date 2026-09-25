from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
from pathlib import Path
import shutil
import hashlib

app = FastAPI(title="Vault Storage System")


# ============================================================
# SIMULATED STORAGE NODES
# ============================================================

NODES = {
    "node1": {"status": "healthy"},
    "node2": {"status": "healthy"},
    "node3": {"status": "healthy"},
    "node4": {"status": "healthy"},
}

STORAGE = Path("storage")


# Create storage folders
for node in NODES:
    (STORAGE / node).mkdir(parents=True, exist_ok=True)


# ============================================================
# CHECKSUM / INTEGRITY
# ============================================================

def get_checksum(file_path):
    sha256 = hashlib.sha256()

    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)

    return sha256.hexdigest()


# ============================================================
# HOME
# ============================================================

@app.get("/")
def home():
    return {
        "system": "VAULT",
        "status": "online",
        "message": "Distributed storage system is running"
    }


# ============================================================
# GET NODE STATUS
# ============================================================

@app.get("/nodes")
def get_nodes():
    return NODES


# ============================================================
# UPLOAD FILE
# Creates 3 replicas
# ============================================================

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):

    filename = file.filename

    # Temporary file
    temp_file = STORAGE / filename

    # Save uploaded file temporarily
    with open(temp_file, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Calculate original checksum
    checksum = get_checksum(temp_file)

    # Replicate to 3 nodes
    replicas = ["node1", "node2", "node3"]

    for node in replicas:

        # Only replicate to healthy nodes
        if NODES[node]["status"] == "healthy":

            destination = STORAGE / node / filename

            shutil.copy2(
                temp_file,
                destination
            )

    # Remove temporary file
    temp_file.unlink()

    return {
        "message": "File uploaded successfully",
        "filename": filename,
        "replicas": replicas,
        "checksum": checksum
    }


# ============================================================
# DOWNLOAD FILE
# Reads from any healthy replica
# ============================================================

@app.get("/download/{filename}")
def download_file(filename: str):

    for node, info in NODES.items():

        file_path = STORAGE / node / filename

        if (
            info["status"] == "healthy"
            and file_path.exists()
        ):

            return FileResponse(
                file_path,
                filename=filename
            )

    return {
        "error": "File unavailable"
    }


# ============================================================
# FAIL NODE
# Simulates complete node failure
# ============================================================

@app.post("/fail/{node}")
def fail_node(node: str):

    if node not in NODES:
        return {
            "error": "Node does not exist"
        }

    # Mark node as failed
    NODES[node]["status"] = "failed"

    # Simulate storage becoming unavailable
    node_folder = STORAGE / node

    if node_folder.exists():

        for file in node_folder.iterdir():

            if file.is_file():
                file.unlink()

    return {
        "message": f"{node} has failed",
        "status": "failed",
        "data": "Replica on failed node is unavailable"
    }


# ============================================================
# REPAIR REPLICA
# Copies a healthy replica to Node 4
# ============================================================

@app.post("/repair/{filename}")
def repair_file(filename: str):

    source = None
    source_node = None

    # Find a healthy replica
    for node, info in NODES.items():

        file_path = STORAGE / node / filename

        if (
            info["status"] == "healthy"
            and file_path.exists()
        ):

            source = file_path
            source_node = node
            break

    # No healthy copy available
    if source is None:

        return {
            "error": "No healthy replica available"
        }

    # Node 4 is our repair target
    repair_node = "node4"

    destination = STORAGE / repair_node / filename

    # Copy healthy replica
    shutil.copy2(
        source,
        destination
    )

    # Verify repaired copy
    repaired_checksum = get_checksum(destination)
    source_checksum = get_checksum(source)

    if repaired_checksum != source_checksum:

        return {
            "error": "Repair failed integrity verification"
        }

    return {
        "message": "Replica repaired successfully",
        "source_node": source_node,
        "new_replica": repair_node,
        "filename": filename,
        "checksum": repaired_checksum,
        "integrity": "verified"
    }


# ============================================================
# VERIFY REPLICA INTEGRITY
# Compares SHA-256 checksums
# ============================================================

@app.get("/verify/{filename}")
def verify_file(filename: str):

    checksums = {}

    # Calculate checksum for every healthy replica
    for node, info in NODES.items():

        file_path = STORAGE / node / filename

        if (
            info["status"] == "healthy"
            and file_path.exists()
        ):

            checksums[node] = get_checksum(
                file_path
            )

    # No replicas available
    if not checksums:

        return {
            "error": "No healthy replica available"
        }

    # Check whether all checksums match
    unique_checksums = set(
        checksums.values()
    )

    if len(unique_checksums) == 1:

        return {
            "status": "integrity_ok",
            "message": "All healthy replicas match",
            "checksums": checksums
        }

    # Different checksums = corruption/inconsistency
    return {
        "status": "corruption_detected",
        "message": "Replica inconsistency detected",
        "checksums": checksums
    }


# ============================================================
# SIMULATE DATA CORRUPTION
# Intentionally modifies one replica
# ============================================================

@app.post("/corrupt/{node}/{filename}")
def corrupt_replica(node: str, filename: str):

    if node not in NODES:

        return {
            "error": "Node does not exist"
        }

    file_path = STORAGE / node / filename

    if not file_path.exists():

        return {
            "error": "Replica does not exist on this node"
        }

    if NODES[node]["status"] != "healthy":

        return {
            "error": "Node is not healthy"
        }

    # Modify the replica
    with open(file_path, "ab") as f:
        f.write(b"\nVAULT_CORRUPTION_TEST")

    corrupted_checksum = get_checksum(
        file_path
    )

    return {
        "message": "Replica corrupted successfully",
        "node": node,
        "filename": filename,
        "new_checksum": corrupted_checksum,
        "status": "corrupted"
    }