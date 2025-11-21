#!/usr/bin/env bash
set -euo pipefail

# Script de récupération des modèles URDF depuis les dépôts publics ROS/ROS-Industrial.
# Il clone en lecture seule, copie les URDF/meshes attendus vers robots/urdf et robots/meshes,
# sans modifier les sources d'origine.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK_DIR="$ROOT_DIR/tmp/robots-fetch"
mkdir -p "$WORK_DIR"

fetch_repo() {
  local url="$1"
  local name="$2"
  if [ ! -d "$WORK_DIR/$name" ]; then
    git clone --depth 1 "$url" "$WORK_DIR/$name"
  fi
}

echo "Clonage des dépôts..."
fetch_repo https://github.com/ros-industrial/fanuc fanuc
fetch_repo https://github.com/ros-industrial/kuka_experimental kuka_experimental
fetch_repo https://github.com/kroshu/kuka_robot_descriptions.git kuka_robot_descriptions
fetch_repo https://github.com/ros-industrial/universal_robot universal_robot
fetch_repo https://github.com/UniversalRobots/Universal_Robots_ROS2_Description ur_ros2

mkdir -p "$ROOT_DIR/robots/urdf/fanuc" "$ROOT_DIR/robots/meshes/fanuc"
mkdir -p "$ROOT_DIR/robots/urdf/kuka" "$ROOT_DIR/robots/meshes/kuka"
mkdir -p "$ROOT_DIR/robots/urdf/universal_robot" "$ROOT_DIR/robots/meshes/universal_robot"

echo "Copie de quelques modèles représentatifs..."
cp -f "$WORK_DIR/fanuc/fanuc_m710ic_support/urdf/m710ic.urdf" "$ROOT_DIR/robots/urdf/fanuc/m710ic.urdf" || true
cp -r "$WORK_DIR/fanuc/fanuc_m710ic_support/meshes" "$ROOT_DIR/robots/meshes/fanuc/m710ic" || true

cp -f "$WORK_DIR/kuka_experimental/kuka_iiwa_support/urdf/iiwa7.urdf.xacro" "$ROOT_DIR/robots/urdf/kuka/iiwa7.urdf.xacro" || true
cp -r "$WORK_DIR/kuka_experimental/kuka_iiwa_support/meshes" "$ROOT_DIR/robots/meshes/kuka/iiwa7" || true

cp -f "$WORK_DIR/universal_robot/ur_description/urdf/ur5.urdf.xacro" "$ROOT_DIR/robots/urdf/universal_robot/ur5.urdf.xacro" || true
cp -r "$WORK_DIR/universal_robot/ur_description/meshes/ur5" "$ROOT_DIR/robots/meshes/universal_robot/ur5" || true

echo "Mise à jour du README robots/sources..."
{
  echo "Modèles récupérés le $(date)"
  echo "- fanuc : https://github.com/ros-industrial/fanuc"
  echo "- kuka_experimental : https://github.com/ros-industrial/kuka_experimental"
  echo "- universal_robot : https://github.com/ros-industrial/universal_robot"
  echo "- Universal_Robots_ROS2_Description : https://github.com/UniversalRobots/Universal_Robots_ROS2_Description"
} > "$ROOT_DIR/robots/sources/README.md"

echo "Fini."
