// =====================
// API Helpers
// =====================
const authToken = localStorage.getItem("authToken");
const headers = {
  Authorization: `Bearer ${authToken}`,
  "Content-Type": "application/json",
};

async function apiGet(path) {
  const res = await fetch(path, { headers });
  if (!res.ok) throw new Error(`GET ${path} failed`);
  return res.json();
}

async function apiPost(path, body) {
  const res = await fetch(path, {
    method: "POST",
    headers,
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    const errorMessage = errorData.detail || `POST ${path} failed`;
    throw new Error(errorMessage);
  }
  return res.json();
}

async function apiPut(path, body) {
  const res = await fetch(path, {
    method: "PUT",
    headers,
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`PUT ${path} failed`);
  return res.json();
}

async function apiDelete(path) {
  const res = await fetch(path, {
    method: "DELETE",
    headers,
  });
  if (!res.ok) throw new Error(`DELETE ${path} failed`);
  return res.json();
}

// =====================
// Page Logic
// =====================

async function displayDeckName(deckId){
  const deck = await apiGet(`/decks/${deckId}`);
  const deckName = deck.name;
  document.getElementById("deck-name").textContent = `${deckName}`
}

async function getNumberOfFlashcards() {
    const queryString = window.location.search; 
    const params = new URLSearchParams(queryString);
    if (params.has("deckId")){
        const deckId = params.get("deckId");
        displayDeckName(deckId);
        const allFlashcards = await apiGet(`/decks/${deckId}/flashcards`);
        const numberofAllFlashcards = allFlashcards.length;
        document.getElementById("all-flashcards").textContent = `${numberofAllFlashcards} total cards`
        
        const dueFlashcards = await apiGet(`/decks/${deckId}/flashcards?due=true`);
        const numberOfDueFlashcards = dueFlashcards.length;
        document.getElementById("due-flashcards").textContent = `${numberOfDueFlashcards} due cards`
    }    
}

async function startReview(){
  const queryString = window.location.search; 
  const params = new URLSearchParams(queryString);
  const deckId = params.get("deckId");
  document.getElementById("review-button").addEventListener("click", () => {
    window.location.href = `review.html?deckId=${deckId}`;
  });
}

async function backToDecks(){
  document.getElementById("back-to-dashboard").addEventListener("click", () => {
    window.location.href = "start.html";
  });
}

async function addFlashcardModal(){
  const flashcardModalButton = document.getElementById("add-flashcard");
  const addFlashCardModal = document.getElementById("add-flashcard-modal");
  flashcardModalButton.addEventListener("click", () => {
    addFlashCardModal.classList.remove("hidden");
  });
}

async function closeModal(){
  const addFlashCardModal = document.getElementById("add-flashcard-modal");
  const cancelButton = document.getElementById("add-flashcard-cancel");
  const llmCancel1 = document.getElementById("llm-cancel-1");
  const llmCancel2 = document.getElementById("llm-cancel-2");

  const closeModalHandler = () => {
    addFlashCardModal.classList.add("hidden");
    resetModalState();
  };

  cancelButton.addEventListener("click", closeModalHandler);
  llmCancel1.addEventListener("click", closeModalHandler);
  llmCancel2.addEventListener("click", closeModalHandler);

  addFlashCardModal.addEventListener("click", (event) => {
    if(event.target === addFlashCardModal){
      closeModalHandler();
    }
  });
  document.addEventListener("keydown", (event) => {
    if(event.key === "Escape" && !addFlashCardModal.classList.contains("hidden")){
      closeModalHandler();
    }
  })
}

function resetModalState() {
  // Reset to LLM tab (default)
  switchToLLMTab();

  // Clear forms
  document.getElementById("add-flashcard-form").reset();
  document.getElementById("llm-text-form").reset();
  document.getElementById("llm-image-form").reset();

  // Hide generated cards preview and loading spinner
  document.getElementById("generated-cards-preview").classList.add("hidden");
  document.getElementById("loading-spinner").classList.add("hidden");
  document.getElementById("image-preview").classList.add("hidden");

  // Reset to text generation sub-tab
  switchToTextGenTab();

  // Clear generated cards
  generatedFlashcards = [];
}

async function addNewCard() {
  const form = document.getElementById("add-flashcard-form");
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const front = document.getElementById("front").value;
    const back = document.getElementById("back").value;
    const params = new URLSearchParams(window.location.search);
    let deckId = null;
    if (params.has("deckId")) {
      deckId = parseInt(params.get("deckId"));
    }
    const body = { front, back, deck_id: deckId };
    try {
      await apiPost("/flashcards", body);
      await getNumberOfFlashcards();
      form.reset();
      // also refresh the table view if it is open
      const showFlashcardsModal = document.getElementById("show-flashcards-modal");
      if (!showFlashcardsModal.classList.contains("hidden")) {
        await showAllFlashcards();
      }
    } catch (err) {
      console.error("Failed to add flashcard:", err);
    }
  });
}

async function showAllFlashcards() {
  const params = new URLSearchParams(window.location.search);
  const deckId = params.get("deckId");
  const flashcards = await apiGet(`/decks/${deckId}/flashcards`);
  const tbody = document.getElementById("flashcards-tbody");
  const rowTemplate = document.getElementById("flashcard-row-template");
  
  tbody.innerHTML = ""; // Clear existing rows

  for (const card of flashcards) {
    const row = rowTemplate.content.cloneNode(true);
    const tr = row.querySelector("tr");
    tr.dataset.flashcardId = card.id;
    row.querySelector(".front").textContent = card.front;
    row.querySelector(".back").textContent = card.back;
    row.querySelector(".next-review").textContent = new Date(card.next_review_at).toLocaleDateString();
    tbody.appendChild(row);
  }

  // Add event listeners for delete and edit buttons
  tbody.querySelectorAll(".delete-btn").forEach(button => {
    button.addEventListener("click", async (event) => {
      const row = event.target.closest("tr");
      const flashcardId = row.dataset.flashcardId;
      try {
        await apiDelete(`/flashcards/${flashcardId}`);
        await getNumberOfFlashcards();
        await showAllFlashcards(); // Refresh the table
      } catch (err) {
        console.error("Failed to delete flashcard:", err);
      }
    });
  });

  tbody.querySelectorAll(".edit-btn").forEach(button => {
    button.addEventListener("click", (event) => {
      const row = event.target.closest("tr");
      const flashcardId = row.dataset.flashcardId;
      const front = row.querySelector(".front").textContent;
      const back = row.querySelector(".back").textContent;
      const nextReview = row.querySelector(".next-review").textContent;

      const editTemplate = document.getElementById("edit-flashcard-row-template");
      const editRowFragment = editTemplate.content.cloneNode(true);
      const editRow = editRowFragment.querySelector('tr');
      
      editRow.querySelector(".front-input").value = front;
      editRow.querySelector(".back-input").value = back;
      editRow.querySelector(".next-review").textContent = nextReview;
      
      row.replaceWith(editRow);

      editRow.querySelector(".save-btn").addEventListener("click", async () => {
        const newFront = editRow.querySelector(".front-input").value;
        const newBack = editRow.querySelector(".back-input").value;
        try {
          await apiPut(`/flashcards/${flashcardId}`, { front: newFront, back: newBack });
          await showAllFlashcards(); // Refresh the table
        } catch (err) {
          console.error("Failed to update flashcard:", err);
        }
      });

      editRow.querySelector(".cancel-edit-btn").addEventListener("click", () => {
        showAllFlashcards(); // Just refresh the table to cancel
      });
    });
  });
}

async function showAllFlashcardsModal() {
  const showFlashcardsButton = document.getElementById("show-flashcards");
  const showFlashcardsModal = document.getElementById("show-flashcards-modal");

  showFlashcardsButton.addEventListener("click", async () => {
    showFlashcardsModal.classList.remove("hidden");
    await showAllFlashcards();
  });
}

async function closeShowAllFlashcardsModal() {
    const showFlashcardsModal = document.getElementById("show-flashcards-modal");
    const cancelButton = document.getElementById("show-flashcards-cancel");

    cancelButton.addEventListener("click", () => {
        showFlashcardsModal.classList.add("hidden");
    });

    showFlashcardsModal.addEventListener("click", (event) => {
        if (event.target === showFlashcardsModal) {
            showFlashcardsModal.classList.add("hidden");
        }
    });

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape" && !showFlashcardsModal.classList.contains("hidden")) {
            showFlashcardsModal.classList.add("hidden");
        }
    });
}

// =====================
// Tab Switching
// =====================

function switchToManualTab() {
  document.getElementById("manual-tab").classList.add("border-blue-500", "text-blue-600");
  document.getElementById("manual-tab").classList.remove("border-transparent", "text-gray-500");
  document.getElementById("llm-tab").classList.remove("border-blue-500", "text-blue-600");
  document.getElementById("llm-tab").classList.add("border-transparent", "text-gray-500");
  document.getElementById("manual-content").classList.remove("hidden");
  document.getElementById("llm-content").classList.add("hidden");
}

function switchToLLMTab() {
  document.getElementById("llm-tab").classList.add("border-blue-500", "text-blue-600");
  document.getElementById("llm-tab").classList.remove("border-transparent", "text-gray-500");
  document.getElementById("manual-tab").classList.remove("border-blue-500", "text-blue-600");
  document.getElementById("manual-tab").classList.add("border-transparent", "text-gray-500");
  document.getElementById("llm-content").classList.remove("hidden");
  document.getElementById("manual-content").classList.add("hidden");
}

function switchToTextGenTab() {
  document.getElementById("text-gen-tab").classList.add("bg-blue-500", "text-white");
  document.getElementById("text-gen-tab").classList.remove("bg-gray-300", "text-gray-800");
  document.getElementById("image-gen-tab").classList.remove("bg-blue-500", "text-white");
  document.getElementById("image-gen-tab").classList.add("bg-gray-300", "text-gray-800");
  document.getElementById("text-gen-content").classList.remove("hidden");
  document.getElementById("image-gen-content").classList.add("hidden");
}

function switchToImageGenTab() {
  document.getElementById("image-gen-tab").classList.add("bg-blue-500", "text-white");
  document.getElementById("image-gen-tab").classList.remove("bg-gray-300", "text-gray-800");
  document.getElementById("text-gen-tab").classList.remove("bg-blue-500", "text-white");
  document.getElementById("text-gen-tab").classList.add("bg-gray-300", "text-gray-800");
  document.getElementById("image-gen-content").classList.remove("hidden");
  document.getElementById("text-gen-content").classList.add("hidden");
}

function setupTabs() {
  document.getElementById("manual-tab").addEventListener("click", switchToManualTab);
  document.getElementById("llm-tab").addEventListener("click", switchToLLMTab);
  document.getElementById("text-gen-tab").addEventListener("click", switchToTextGenTab);
  document.getElementById("image-gen-tab").addEventListener("click", switchToImageGenTab);
}

// =====================
// LLM Flashcard Generation
// =====================

let generatedFlashcards = [];

async function generateFromText() {
  const form = document.getElementById("llm-text-form");
  const loadingSpinner = document.getElementById("loading-spinner");
  const generateBtn = document.getElementById("text-generate-btn");

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const text = document.getElementById("llm-text-input").value;
    const numCards = parseInt(document.getElementById("text-num-cards").value);
    const params = new URLSearchParams(window.location.search);
    let deckId = null;
    if (params.has("deckId")) {
      deckId = parseInt(params.get("deckId"));
    }

    // Show loading spinner
    loadingSpinner.classList.remove("hidden");
    generateBtn.disabled = true;
    document.getElementById("generated-cards-preview").classList.add("hidden");

    try {
      const response = await apiPost("/llm/generate-from-text", {
        text,
        num_cards: numCards,
        deck_id: deckId
      });

      generatedFlashcards = response.flashcards;
      displayGeneratedFlashcards();
    } catch (err) {
      console.error("Failed to generate flashcards from text:", err);
      alert(err.message || "Failed to generate flashcards. Please try again.");
    } finally {
      loadingSpinner.classList.add("hidden");
      generateBtn.disabled = false;
    }
  });
}

async function generateFromImage() {
  const form = document.getElementById("llm-image-form");
  const imageInput = document.getElementById("llm-image-input");
  const previewContainer = document.getElementById("image-preview");
  const previewImg = document.getElementById("preview-img");
  const loadingSpinner = document.getElementById("loading-spinner");
  const generateBtn = document.getElementById("image-generate-btn");

  // Image preview
  imageInput.addEventListener("change", (event) => {
    const file = event.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        previewImg.src = e.target.result;
        previewContainer.classList.remove("hidden");
      };
      reader.readAsDataURL(file);
    }
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const file = imageInput.files[0];
    if (!file) {
      alert("Please select an image");
      return;
    }

    const numCards = parseInt(document.getElementById("image-num-cards").value);
    const params = new URLSearchParams(window.location.search);
    let deckId = null;
    if (params.has("deckId")) {
      deckId = parseInt(params.get("deckId"));
    }

    // Show loading spinner
    loadingSpinner.classList.remove("hidden");
    generateBtn.disabled = true;
    document.getElementById("generated-cards-preview").classList.add("hidden");

    try {
      // Convert image to base64
      const base64 = await fileToBase64(file);
      const base64Data = base64.split(',')[1]; // Remove data:image/xxx;base64, prefix

      const response = await apiPost("/llm/generate-from-image", {
        image_base64: base64Data,
        num_cards: numCards,
        deck_id: deckId
      });

      generatedFlashcards = response.flashcards;
      displayGeneratedFlashcards();
    } catch (err) {
      console.error("Failed to generate flashcards from image:", err);
      alert(err.message || "Failed to generate flashcards. Please try again.");
    } finally {
      loadingSpinner.classList.add("hidden");
      generateBtn.disabled = false;
    }
  });
}

function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

function displayGeneratedFlashcards() {
  const container = document.getElementById("generated-cards-list");
  container.innerHTML = "";

  generatedFlashcards.forEach((card, index) => {
    const cardDiv = document.createElement("div");
    cardDiv.className = "p-3 border rounded bg-gray-50";
    cardDiv.dataset.cardIndex = index;

    if (card.editing) {
      // Edit mode
      cardDiv.innerHTML = `
        <div class="font-semibold text-sm text-gray-700 mb-2">Card ${index + 1}</div>
        <div class="space-y-2">
          <div>
            <label class="text-xs text-gray-600">Front:</label>
            <input type="text" class="edit-front w-full px-2 py-1 border rounded text-sm" value="${escapeHtml(card.front)}">
          </div>
          <div>
            <label class="text-xs text-gray-600">Back:</label>
            <textarea class="edit-back w-full px-2 py-1 border rounded text-sm" rows="2">${escapeHtml(card.back)}</textarea>
          </div>
          <div class="flex gap-2">
            <button class="save-card-btn flex-1 bg-green-500 hover:bg-green-600 text-white text-xs font-bold py-1 px-2 rounded">Save</button>
            <button class="cancel-edit-btn flex-1 bg-gray-300 hover:bg-gray-400 text-gray-800 text-xs font-bold py-1 px-2 rounded">Cancel</button>
          </div>
        </div>
      `;
    } else {
      // View mode
      cardDiv.innerHTML = `
        <div class="font-semibold text-sm text-gray-700">Card ${index + 1}</div>
        <div class="mt-1 text-sm"><strong>Front:</strong> ${escapeHtml(card.front)}</div>
        <div class="mt-1 text-sm"><strong>Back:</strong> ${escapeHtml(card.back)}</div>
        <div class="flex gap-2 mt-2">
          <button class="edit-card-btn flex-1 bg-yellow-500 hover:bg-yellow-600 text-white text-xs font-bold py-1 px-2 rounded">Edit</button>
          <button class="discard-card-btn flex-1 bg-red-500 hover:bg-red-600 text-white text-xs font-bold py-1 px-2 rounded">Discard</button>
        </div>
      `;
    }

    container.appendChild(cardDiv);
  });

  // Add event listeners for individual card actions
  container.querySelectorAll(".edit-card-btn").forEach(btn => {
    btn.addEventListener("click", (e) => {
      const index = parseInt(e.target.closest("[data-card-index]").dataset.cardIndex);
      generatedFlashcards[index].editing = true;
      displayGeneratedFlashcards();
    });
  });

  container.querySelectorAll(".save-card-btn").forEach(btn => {
    btn.addEventListener("click", (e) => {
      const cardDiv = e.target.closest("[data-card-index]");
      const index = parseInt(cardDiv.dataset.cardIndex);
      const newFront = cardDiv.querySelector(".edit-front").value;
      const newBack = cardDiv.querySelector(".edit-back").value;
      generatedFlashcards[index].front = newFront;
      generatedFlashcards[index].back = newBack;
      generatedFlashcards[index].editing = false;
      displayGeneratedFlashcards();
    });
  });

  container.querySelectorAll(".cancel-edit-btn").forEach(btn => {
    btn.addEventListener("click", (e) => {
      const index = parseInt(e.target.closest("[data-card-index]").dataset.cardIndex);
      generatedFlashcards[index].editing = false;
      displayGeneratedFlashcards();
    });
  });

  container.querySelectorAll(".discard-card-btn").forEach(btn => {
    btn.addEventListener("click", (e) => {
      const index = parseInt(e.target.closest("[data-card-index]").dataset.cardIndex);
      generatedFlashcards.splice(index, 1);
      displayGeneratedFlashcards();

      // Hide preview if no cards left
      if (generatedFlashcards.length === 0) {
        document.getElementById("generated-cards-preview").classList.add("hidden");
      }
    });
  });

  document.getElementById("generated-cards-preview").classList.remove("hidden");
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

async function saveGeneratedCards() {
  const saveButton = document.getElementById("save-generated-cards");
  saveButton.addEventListener("click", async () => {
    const params = new URLSearchParams(window.location.search);
    let deckId = null;
    if (params.has("deckId")) {
      deckId = parseInt(params.get("deckId"));
    }

    const numCards = generatedFlashcards.length;

    try {
      for (const card of generatedFlashcards) {
        await apiPost("/flashcards", {
          front: card.front,
          back: card.back,
          deck_id: deckId
        });
      }

      await getNumberOfFlashcards();
      generatedFlashcards = [];
      document.getElementById("add-flashcard-modal").classList.add("hidden");
      resetModalState();

      // Refresh table if open
      const showFlashcardsModal = document.getElementById("show-flashcards-modal");
      if (!showFlashcardsModal.classList.contains("hidden")) {
        await showAllFlashcards();
      }

      alert(`Successfully saved ${numCards} flashcards!`);
    } catch (err) {
      console.error("Failed to save generated flashcards:", err);
      alert("Failed to save some flashcards. Please try again.");
    }
  });
}

async function discardGeneratedCards() {
  const discardButton = document.getElementById("discard-generated-cards");
  discardButton.addEventListener("click", () => {
    generatedFlashcards = [];
    document.getElementById("generated-cards-preview").classList.add("hidden");
    document.getElementById("llm-text-form").reset();
    document.getElementById("llm-image-form").reset();
  });
}

// =====================
// Init
// =====================

document.addEventListener("DOMContentLoaded", async () => {
  if (!authToken) {
    window.location.href = "login.html";
    return;
  }
  try {
    await getNumberOfFlashcards();
    await startReview();
    await backToDecks();
    await addFlashcardModal();
    await closeModal();
    await addNewCard();
    await showAllFlashcardsModal();
    await closeShowAllFlashcardsModal();
    setupTabs();
    await generateFromText();
    await generateFromImage();
    await saveGeneratedCards();
    await discardGeneratedCards();
  } catch (err) {
    console.error(err);
  }
});