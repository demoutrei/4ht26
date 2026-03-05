const idNumberInput = document.querySelector("#form-idNumber-input");
const passwordInput = document.querySelector("#form-password-input");
const fullLegalNameInput = document.querySelector("#form-fullName-input");
const createAccountButton = document.querySelector("#createAccount-button");
const loginRedirectText = document.querySelector("#subtext-login-redirect");
const userTypeOptionsArray = document.querySelectorAll(".form-userType-option");


userTypeOptionsArray.forEach(
  optionSelected => {
    optionSelected.addEventListener("click", (_) => {
      userTypeOptionsArray.forEach(
        option => {
          optionSelected.getAttribute("id") == option.getAttribute("id") ? option.classList.add("selected") : option.classList.remove("selected");
        }
      )
    })
  }
)


loginRedirectText.addEventListener("click", (_) => {
  window.open('./login', "_self");
})


createAccountButton.addEventListener("click", (_) => {
  if ((!idNumberInput.value) || (!passwordInput.value) || (!fullLegalNameInput.value)) return;
  if (document.querySelectorAll(".form-userType-option.selected").length != 1) return;
  fetch(
    `http://127.0.0.1:8000/api/v1/users/`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        "_id": idNumberInput.value,
        "full_name": fullLegalNameInput.value,
        "password": passwordInput.value,
        "user_type": document.querySelector(".form-userType-option.selected").dataset.value
      })
    }
  ).then(
    response => response.json()
  ).then(
    _ => window.open('./login', "_self")
  )
})