const form = document.querySelector("#updateForm");
const submitButton = document.querySelector("#submitButton");
const resultSection = document.querySelector("#resultSection");
const openSheetButton = document.querySelector("#openSheetButton");
const resultDescription = document.querySelector("#resultDescription");
const alertBox = document.querySelector("#alert");
const alertMessage = document.querySelector("#alertMessage");
const closeAlert = document.querySelector("#closeAlert");
const steps = [...document.querySelectorAll("#processSteps li")];

const metrics = {
  responses: document.querySelector("#metricResponses"),
  performed: document.querySelector("#metricPerformed"),
  never: document.querySelector("#metricNever"),
  knowledge: document.querySelector("#metricKnowledge"),
  knowledgeHpv: document.querySelector("#metricKnowledgeHpv"),
};

let progressTimers = [];

function setStep(activeIndex) {
  steps.forEach((step, index) => {
    step.classList.toggle("is-complete", index < activeIndex);
    step.classList.toggle("is-active", index === activeIndex);
  });
}

function completeSteps() {
  steps.forEach((step) => {
    step.classList.remove("is-active");
    step.classList.add("is-complete");
  });
}

function resetSteps() {
  progressTimers.forEach(window.clearTimeout);
  progressTimers = [];
  steps.forEach((step) => {
    step.classList.remove("is-active", "is-complete");
  });
}

function startProgress() {
  resetSteps();
  setStep(0);
  [1, 2, 3].forEach((stepIndex, index) => {
    progressTimers.push(
      window.setTimeout(() => setStep(stepIndex), 850 * (index + 1))
    );
  });
}

function setLoading(isLoading) {
  submitButton.classList.toggle("is-loading", isLoading);
  submitButton.disabled = isLoading;
  [...form.elements].forEach((element) => {
    if (element !== submitButton) {
      element.disabled = isLoading;
    }
  });
}

function showAlert(message) {
  alertMessage.textContent = message;
  alertBox.hidden = false;
}

function hideAlert() {
  alertBox.hidden = true;
}

function animateNumber(element, target) {
  const duration = 650;
  const startTime = performance.now();

  function update(now) {
    const progress = Math.min((now - startTime) / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    element.textContent = Math.round(target * eased).toLocaleString("pt-BR");
    if (progress < 1) {
      requestAnimationFrame(update);
    }
  }

  requestAnimationFrame(update);
}

function displayResult(result) {
  animateNumber(metrics.responses, result.total_respostas);
  animateNumber(metrics.performed, result.total_ja_realizaram);
  animateNumber(metrics.never, result.total_nunca_realizaram);
  animateNumber(metrics.knowledge, result.total_conhecem);
  animateNumber(metrics.knowledgeHpv, result.total_conhecem_hpv);

  resultDescription.textContent =
    `${result.total_linhas_tabela} linhas foram atualizadas na aba ` +
    `"${result.nome_aba_destino}", usando dados de "${result.nome_aba_origem}".`;
  openSheetButton.href = result.link_planilha;
  resultSection.hidden = false;
  window.setTimeout(() => {
    resultSection.scrollIntoView({ behavior: "smooth", block: "start" });
  }, 120);
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  hideAlert();
  resultSection.hidden = true;
  setLoading(true);
  startProgress();

  const payload = {
    planilha: form.planilha.value,
    gid_origem: form.gid_origem.value,
    aba_destino: form.aba_destino.value,
  };

  try {
    const response = await fetch("/api/atualizar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await response.json();

    if (!response.ok || !data.sucesso) {
      throw new Error(data.mensagem || "Não foi possível concluir a atualização.");
    }

    progressTimers.forEach(window.clearTimeout);
    completeSteps();
    displayResult(data.resultado);
  } catch (error) {
    resetSteps();
    showAlert(error.message);
  } finally {
    setLoading(false);
  }
});

closeAlert.addEventListener("click", hideAlert);
