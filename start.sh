#!/bin/bash
# This script is designed to be run on Unix/Linux systems (like macOS or Ubuntu)

# ----------------------------------------------------
# Set current directory to the location of this script
# $0 is the path to the script. dirname gets the directory.
# This ensures that 'cd backend', 'cd gateway', etc., work regardless
# of where the user executes the script from.
# ----------------------------------------------------
cd "$(dirname "$0")"

# ----------------------------------------------------
# PARAMETER CHECK: Check if the "headless" argument is provided
# ----------------------------------------------------
GATEWAY_SCRIPT="gateway.py"
if [ "$1" = "headless" ]; then
    GATEWAY_SCRIPT="gateway_headless.py"
    echo "[INFO] Running gateway in HEADLESS mode."
else
    echo "[INFO] Running gateway in default mode. To use headless mode, run: ./start_system.sh headless"
fi

echo ""
echo "===================================================="
echo "               STARTING SERVICES"
echo "===================================================="

# Helper function to run a service in the background
# It isolates the service's environment so 'cd' and 'source' don't affect the main script.
start_service() {
    (
        SERVICE_NAME="$1"
        DIR="$2"
        COMMAND="$3"

        echo "[INFO] Starting $SERVICE_NAME..."
        cd "$DIR" || { echo "Error: Failed to change to $DIR directory."; exit 1; }
        
        # Activate virtual environment (uses bin/activate path on Unix/Linux)
        source .venv/bin/activate || { echo "Error: Failed to activate virtual environment in $DIR."; exit 1; }
        
        # Execute the command and send it to the background
        eval "$COMMAND" &
        
        # Store the PID of the background job
        PID=$!
        echo "   -> PID: $PID"
    )
}

# ----------------------------------------------------
# 1. START BACKEND SERVICE (Uvicorn)
# ----------------------------------------------------
start_service "Backend (Uvicorn)" "backend" "uvicorn api:app --reload"


# ----------------------------------------------------
# 2. START GATEWAY SERVICE (Python)
# ----------------------------------------------------
# The gateway process needs to run in the current shell's subprocess, so we can't use the simple
# start_service function above if we want to track its PID easily in the main script.
echo "[INFO] Starting Gateway ($GATEWAY_SCRIPT)..."
(
    cd gateway
    source .venv/bin/activate
    python "$GATEWAY_SCRIPT"
) &
GATEWAY_PID=$!
echo "   -> PID: $GATEWAY_PID"


# ----------------------------------------------------
# 3. BUILD AND START FRONTEND PREVIEW
# ----------------------------------------------------

echo ""
echo "[INFO] Switching to frontend directory to build..."
cd frontend || { echo "Error: Failed to change to frontend directory."; exit 1; }

echo "[3/3] Running pnpm build (this may take a moment)..."
pnpm build

echo "[3/3] Starting Frontend Preview..."
# Run preview in background
pnpm preview &
FRONTEND_PID=$!
echo "   -> PID: $FRONTEND_PID"

# Switch back to the root directory
cd ..

echo ""
echo "===================================================="
echo "                LAUNCH COMPLETE"
echo "===================================================="
echo "All servers are running in the background."
echo "You may need to run 'fg' to bring the last process (Frontend Preview) to the foreground."
echo "To stop all services, you can run a kill command using their PIDs (Process IDs)."
echo "Press Ctrl+C to stop the last background job (pnpm preview)."
