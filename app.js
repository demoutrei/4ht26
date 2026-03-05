import express from 'express';


const app = express();
const host = "127.0.0.1";
const port = 5500;
const apiBaseUrl = "http://127.0.0.1:8000/api/v1";


app.use(express.static('build'));
app.set("view engine", "ejs");
app.set("views", "./build/templates");


app.get('/signup', (request, response) => {
  response.render("signup");
})

app.get('/login', (_, response) => {
  response.render("login");
})

app.get('/u/:userId/dashboard', async (request, response) => {
  const userId = request.params.userId;
  const instances = await (await fetch(`${apiBaseUrl}/users/${userId}/workflows/instances`)).json();
  return response.render("dashboard", {instances: instances});
})

app.get('/u/:userId/workflows', (request, response) => {
  const userId = request.params.userId;
  getUser(userId).then(data => response.render("workflows", data));
})

app.get('/u/:userId/workflows/:workflowId', (request, response) => {
  const userId = request.params.userId;
  const workflowId = request.params.workflowId;
  return response.render("workflow");
})

app.get('/u/:userId/workflows/:workflowId/trigger', (request, response) => {
  const userId = request.params.userId;
  const workflowId = request.params.workflowId;
  fetch(
    `${apiBaseUrl}/users/${userId}/workflows/${workflowId}/trigger`,
    {
      method: "POST"
    }
  ).then(
    response => response.json()
  ).then(
    data => {
      return response.redirect(`/u/${data.user_id}/workflows/${data.workflow_id}/${data.instance_id}`)
    }
  )
})

app.get('/u/:userId/workflows/:workflowId/:workflowInstanceId', (request, response) => {
  const userId = request.params.userId;
  const workflowId = request.params.workflowId;
  const workflowInstanceId = request.params.workflowInstanceId;
  return response.render("workflow_instance");
})


app.listen(port, host, () => {
  console.log(`Running on http://${host}:${port}`);
})


async function getUser(userId) {
  const response = await fetch(`${apiBaseUrl}/users/${userId}`);
  return await response.json();
}