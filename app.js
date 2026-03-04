import express from 'express';


const app = express();
const port = 5500;
const apiBaseUrl = "http://127.0.0.1:8000/api/v1";


app.use(express.static('build'));
app.set("view engine", "ejs");
app.set("views", "./build/templates");


app.get('/u/:userId/dashboard', (request, response) => {
  const userId = request.params.userId;
  getUser(userId).then(data => {
    console.log(data);
  })
  response.render('dashboard');
})


app.listen(port, "127.0.0.1", () => {
  console.log("listening");
})


async function getUser(userId) {
  const response = await fetch(`${apiBaseUrl}/users/${userId}`);
  return await response.json();
}