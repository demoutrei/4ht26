import 'https://cdn.jsdelivr.net/gh/jerosoler/Drawflow/dist/drawflow.min.js';


const drawflowCanvas = document.querySelector("#drawflow-canvas");
const editor = new Drawflow(drawflowCanvas);
editor.start();
editor.line_path = 1;


editor.on("nodeCreated", (id) => {
  console.log(`Node created with ID: ${id}`);
})


const mockData = [
  {
    "_id": 1,
    "name": "Sample Node Name",
    "outputNodes": {
      "1": [2, 3]
    }
  },
  {
    "_id": 2,
    "name": "Sample Node Name 2",
    "inputNodes": {
      "1": [1]
    }
  },
  {
    "_id": 3,
    "name": "Sample Node Name 3",
    "inputNodes": {
      "1": [1]
    }
  }
]


function renderNodes(nodes) {
  for (const index in nodes) {
    const node = nodes[index];
    createNode(node);
  }
  for (const index in nodes) {
    const node = nodes[index];
    renderConnections(node);
  }
}


function createNode(data) {
  editor.addNode(
    data.name,
    Object.keys(data.inputNodes ?? {}).length, Object.keys(data.outputNodes ?? {}).length,
    275 * (data._id), 20,
    "sample-node",
    data,
    `${data.name}`
  );
}


function renderConnections(node) {
  for (const output in node.outputNodes) {
    const outputNodeIds = node.outputNodes[output];
    for (const outputNodeIdsIndex in outputNodeIds) {
      const outputNodeId = outputNodeIds[outputNodeIdsIndex];
      const outputNode = mockData[outputNodeId - 1];
      const outputNodeInputNodes = outputNode.inputNodes ?? {};
      for (const input in outputNodeInputNodes) {
        if (outputNodeInputNodes[input].includes(node._id)) {
          editor.addConnection(node._id, outputNodeId, `output_${parseInt(output)}`, `input_${input}`);
        }
      }
    }
  }
}


renderNodes(mockData);