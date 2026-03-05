const historyNavigator = document.querySelector("#navigator-history");
const workflowsNavigator = document.querySelector("#navigator-workflows");

const workflowTemplatesArray = document.querySelectorAll(".workflowTemplate");


historyNavigator.addEventListener("click", (_) => {
  window.open('./history', "_self");
})

workflowsNavigator.addEventListener("click", (_) => {
  window.open('./workflows', "_self");
})


workflowTemplatesArray.forEach(workflowTemplate => {
  const workflowId = workflowTemplate.dataset.workflowId;
  workflowTemplate.addEventListener("click", (_) => {
    window.open(`./workflows/${workflowId}`, "_self");
  })
})