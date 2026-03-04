import express from 'express';


const app = express();
const port = 5500;


app.use(express.static('build'));
app.set("view engine", "ejs");
app.set("views", "./build/templates");


app.get('/u/:userId/dashboard', (request, response) => {
  const userId = request.params.userId;
  response.render('dashboard');
})


app.listen(port, "127.0.0.1", () => {
  console.log("listening");
})