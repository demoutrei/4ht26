import express from 'express';


const app = express();
const host = "127.0.0.1";
const port = 5500;
const apiBaseUrl = "http://127.0.0.1:8000/api/v1";


app.use(express.static('build'));
app.set("view engine", "ejs");
app.set("views", "./build/templates");


app.get('/u/:userId/dashboard', (request, response) => {
  const userId = request.params.userId;
  getUser(userId).then(data => response.render("dashboard", data));
  createUser(userId, "Sample Full Name", "password123").then(data => console.log(data));
})

app.get('/u/:userId/workflows', (request, response) => {
  const userId = request.params.userId;
  getUser(userId).then(data => response.render("workflows", data));
})

app.get('/u/:userId/workflows/:workflowId'), (request, response) => {
  const userId = request.params.userId;
  const workflowId = request.params.workflowId;
}

app.get('/u/:userId/workflows/:workflowId/:workflowInstanceId', (request, response) => {
  const userId = request.params.userId;
  const workflowId = request.params.workflowId;
  const workflowInstanceId = request.params.workflowInstanceId;
})

app.get('/u/:userId/history', (request, response) => {
  const userId = request.params.userId;
})


app.listen(port, host, () => {
  console.log(`Running on http://${host}:${port}`);
})


async function createUser(userId, fullName, password) {
  const response = await fetch(
    `${apiBaseUrl}/users/`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: {
        "_id": userId,
        "full_name": fullName,
        "password": password
      }
    }
  );
  return await response.json();
}


async function getUser(userId) {
  const response = await fetch(`${apiBaseUrl}/users/${userId}`);
  return await response.json();
}