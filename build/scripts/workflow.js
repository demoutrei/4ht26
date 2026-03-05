import 'https://cdn.jsdelivr.net/gh/jerosoler/Drawflow/dist/drawflow.min.js';


const drawflowCanvas = document.querySelector("#drawflow-canvas");
const editor = new Drawflow(drawflowCanvas);
editor.start();

const dashboardNavigation = document.querySelector("#navigation-dashboard-button");


const workflowNodes = [
  {
    "node_id": 1,
    "name": "Form",
    "node_type": "form",
    "children": [
      {
        "node_id": 2,
        "name": "Scheduling",
        "node_type": "process",
        "children": [
          {
            "node_id": 3,
            "name": "Registration",
            "node_type": "process",
            "children": [
              {
                "node_id": 4,
                "name": "Confirmation",
                "node_type": "process"
              },
              {
                "node_id": 5,
                "name": "Payment Processing",
                "node_type": "process"
              }
            ]
          }
        ]
      }
    ]
  }
]


function createNode(nodeData, xRank, yRank, inputNodeCount) {
  editor.addNode(
    nodeData.name,
    inputNodeCount, (0 < (nodeData.children ?? []).length) ? 1 : 0,
    (250 * (xRank)) + 50, (100 * yRank) + 100,
    `${nodeData.node_type} node`,
    nodeData,
    nodeData.name
  )
}


function renderNode(nodeData, xRank, yRank, inputNodeCount) {
  createNode(nodeData, xRank, yRank, inputNodeCount);
  const children = nodeData.children ?? [];
  for (let i = 0; i < children.length; i++) {
    const childData = children[i];
    renderNode(childData, xRank + 1, i, 1);
    editor.addConnection(nodeData.node_id, childData.node_id, `output_1`, `input_1`);
  }
}


workflowNodes.forEach(
  nodeData => renderNode(nodeData, 0, 0, 0)
)


dashboardNavigation.addEventListener("click", (_) => {
  window.open('../dashboard', "_self");
})