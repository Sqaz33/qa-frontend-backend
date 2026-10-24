"use strict";
const form = document.querySelector("#application-form");
const result = document.querySelector("#result");
const submitButton = form.querySelector("button");
const refreshButton = document.querySelector("#refresh");
const listStatus = document.querySelector("#list-status");
const rows = document.querySelector("#applications");
const amountFormatter = new Intl.NumberFormat("ru-RU", {maximumSignificantDigits: 2});

function showResult(title, message, error = false) {
  result.replaceChildren();
  result.className = error ? "error" : "";
  const heading = document.createElement("strong");
  heading.textContent = title;
  const description = document.createElement("span");
  description.textContent = message;
  result.append(heading, description);
  result.hidden = false;
}

async function refreshList() {
  refreshButton.disabled = true;
  listStatus.textContent = "Загрузка…";
  try {
    const response = await fetch("/api/applications", {cache: "no-store"});
    if (!response.ok) throw new Error("Не удалось прочитать список");
    const data = await response.json();
    rows.replaceChildren();
    for (const item of data.items) {
      const row = document.createElement("tr");
      for (const text of [item.id, item.name, amountFormatter.format(item.amount), "Новая"]) {
        const cell = document.createElement("td");
        cell.textContent = String(text);
        row.append(cell);
      }
      rows.append(row);
    }
    listStatus.textContent = data.items.length ? "Всего заявок: " + data.items.length : "Заявок пока нет";
  } catch (error) {
    rows.replaceChildren();
    listStatus.textContent = "Не удалось загрузить список. Повторите обновление.";
    console.error("Список заявок:", error);
  } finally {
    refreshButton.disabled = false;
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const payload = {
    name: form.elements.name.value.trim(),
    amount: Number(form.elements.amount.value),
    consent: form.elements.consent.checked
  };
  result.hidden = true;
  submitButton.disabled = true;
  try {
    const response = await fetch("/api/applications", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(payload)
    });
    const data = await response.json();
    if (response.ok) {
      showResult("Заявка №" + data.id + " создана",
        data.name + " · Сумма: " + amountFormatter.format(data.amount) + " ₽ · Статус: новая");
      await refreshList();
    } else {
      showResult("Заявка не создана",
        data.fields ? Object.values(data.fields).join(". ") : data.message || "Ошибка сервера", true);
    }
  } catch (error) {
    showResult("Результат не подтверждён",
      "Не удалось получить ответ. Проверьте список перед повторной отправкой заявки.", true);
    console.error("Создание заявки:", error);
  } finally {
    submitButton.disabled = false;
  }
});

refreshButton.addEventListener("click", refreshList);
fetch("/health", {cache: "no-store"})
  .then((response) => { if (!response.ok) throw new Error("Нет версии"); return response.json(); })
  .then((data) => { document.querySelector("#build").textContent = data.build; })
  .catch(() => { document.querySelector("#build").textContent = "версия недоступна"; });
refreshList();
