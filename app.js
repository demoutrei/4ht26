import { BaseHTML } from './base.js';


import express from 'express';
const app = express();
const port = 5500;


app.set("view engine", "ejs");


app.get("/dashboard/workflows/:workflowId", (request, response) => {
  console.log(request.params.workflowId);
  response.render("dashboard/workflows", (error, html) => {
    console.log(html);
    response.send(html);
  })
})


app.listen(port, "127.0.0.1", () => {
  console.log("listening");
})