"use strict";
const form = document.querySelector("#application-form");
const result = document.querySelector("#result");
const button = form.querySelector("button");
form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const payload = {
    name: form.elements.name.value.trim(),
    amount: Number(form.elements.amount.value),
    consent: form.elements.consent.checked
  };
  result.hidden = true;
  button.disabled = true;
  try {
    const response = await fetch("/api/applications", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(payload)
    });
    const data = await response.json();
    result.replaceChildren();
    result.className = response.ok ? "" : "error";
    const heading = document.createElement("strong");
    const description = document.createElement("span");
    if (response.ok) {
      heading.textContent = "Заявка №" + data.id + " создана";
      description.textContent = "Сумма: " + data.amount.toLocaleString("ru-RU") + " ₽ · Статус: новая";
    } else {
      heading.textContent = "Заявка не создана";
      description.textContent = data.fields ? Object.values(data.fields).join(". ") : data.message || "Ошибка сервера";
    }
    result.append(heading, description);
    result.hidden = false;
  } catch (error) {
    result.className = "error";
    result.textContent = "Не удалось получить результат. Проверьте соединение; перед повторной отправкой уточните, создалась ли заявка.";
    result.hidden = false;
    console.error("Ошибка запроса заявки:", error);
  } finally {
    button.disabled = false;
  }
});
