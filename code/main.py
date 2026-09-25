from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import shutil

app = FastAPI(title="Nexus Storage System")

# Our simulated storage nodes
NODES = {
    "node1": {"status": "healthy"},
    "node2": {"status": "healthy"},
    "node3": {"status": "healthy"},
    "node4": {"status": "healthy"},
}

STORAGE = Path("storage")

# Create folders for each node
for node in NODES:
    (STORAGE / node).mkdir(parents=True, exist_ok=True)


@app.get("/")
def home():
    return {
        "system": "NEXUS",
        "status": "online",
        "message": "Distributed storage system is running"
    }


@app.get("/nodes")
def get_nodes():
    return NODES


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    filename = file.filename

    # Temporarily save uploaded file
    temp_file = STORAGE / filename

    with open(temp_file, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Create 3 replicas
    replicas = ["node1", "node2", "node3"]

    for node in replicas:
        destination = STORAGE / node / filename
        shutil.copy2(temp_file, destination)

    # Remove temporary file
    temp_file.unlink()

    return {
        "message": "File uploaded successfully",
        "filename": filename,
        "replicas": replicas
    }


@app.get("/download/{filename}")
def download_file(filename: str):

    # Find a healthy node containing the file
    for node, info in NODES.items():
        file_path = STORAGE / node / filename

        if info["status"] == "healthy" and file_path.exists():
            return FileResponse(
                file_path,
                filename=filename
            )

    return {"error": "File unavailable"}


@app.post("/fail/{node}")
def fail_node(node: str):

    if node not in NODES:
        return {"error": "Node does not exist"}

    NODES[node]["status"] = "failed"

    # Simulate the node's storage becoming unavailable
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


@app.post("/repair/{filename}")
def repair_file(filename: str):

    # Find any healthy node that has the file
    source = None
    source_node = None

    for node, info in NODES.items():
        file_path = STORAGE / node / filename

        if info["status"] == "healthy" and file_path.exists():
            source = file_path
            source_node = node
            break

    if source is None:
        return {
            "error": "No healthy replica available"
        }

    # Put the repaired replica on Node 4
    repair_node = "node4"
    destination = STORAGE / repair_node / filename

    shutil.copy2(source, destination)

    return {
        "message": "Replica repaired successfully",
        "source_node": source_node,
        "new_replica": repair_node,
        "filename": filename
    }