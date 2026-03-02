import 'https://cdn.jsdelivr.net/gh/jerosoler/Drawflow/dist/drawflow.min.js';


const drawflowCanvas = document.querySelector("#drawflow-canvas");
const editor = new Drawflow(drawflowCanvas);
editor.start();
editor.line_path = 1;


editor.on("nodeCreated", (id) => {
  console.log(id);
})


editor.addNode(
  "Sample Node",
  0, 1,
  100, 100,
  "sample-node",
  {
    "name": "Test"
  },
  `test`
);

editor.addNode(
  "Another Sample Node",
  1, 0,
  200, 200,
  "sample-node",
  {
    "name": "Test 2"
  },
  `test 2`
)

editor.addNode(
  "Another Another Sample Node",
  1, 0,
  300, 300,
  "sample-node",
  {},
  `test 3`
)


editor.addConnection(1, 2, "output_1", "input_1");
editor.addConnection(1, 3, "output_1", "input_1");