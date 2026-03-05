import express from 'express';


const app = express();
const port = 5500;
const apiBaseUrl = "http://127.0.0.1:8000/api/v1";


app.use(express.static('build'));
app.set("view engine", "ejs");
app.set("views", "./build/templates");


app.get('/u/:userId/dashboard', async (request, response) => {
  const userId = request.params.userId;
  
  try {
    // First try to create the user
    await fetch(
      `http://127.0.0.1:8000/api/v1/users/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          "_id": parseInt(userId),
          "full_name": "John Doe",
          "password": "password123",
        })
      }
    );
    
    // Then fetch the user data
    const data = await getUser(userId);
    response.render("dashboard", data);
  } catch (err) {
    console.error("Error:", err.message);
    response.status(500).send(`Error: ${err.message}`);
  }
});


app.listen(port, "127.0.0.1", () => {
  console.log("listening");
})


async function getUser(userId) {
  try {
    const response = await fetch(`${apiBaseUrl}/users/${userId}`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();
    if (data.error) {
      throw new Error(data.error);
    }
    return data;
  } catch (error) {
    console.error("Fetch error in getUser:", error);
    throw error;
  }
}