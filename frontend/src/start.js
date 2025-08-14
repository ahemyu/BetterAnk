document.addEventListener("DOMContentLoaded", async () => {

    const authToken = localStorage.getItem("authToken");
    const header = {"Authorization": `Bearer ${authToken}`, "Content-Type": "application/json"}
    if(!authToken){
        // if no auth token redirect to login page
        window.location.href = "login.html";
        return;
    }
    try {
        //////////////// Greet the User ///////////////////////
        //call /me endpoint to get the current user
        const response = await fetch(
            "/me",{
                method: "GET",
                headers: header
            });
        if(!response.ok){
            // token invalid, delete current one and redirect to login
            localStorage.removeItem("authToken");
            window.location.href = "login.html";
            return;
        }

        const user = await response.json();
        document.getElementById("welcome-message").textContent = `Welcome, ${user.username}!`

    }catch (error){
        console.error("Error fetching user: ", error);
        localStorage.removeItem("authToken");
        window.location.href = "login.html";
    } 
        ///////////////// Display Current Decks ///////////////////////////
        // Now we want to display the decks of the current user in a list format
        // for that we need to do a get on /decks
    try {
        const decksResponse = await fetch(
            "/decks", {
                method: "GET",
                headers : header
            });
        if(!decksResponse.ok){
            console.error("Error while fetching decks");
        }
        const decks = await decksResponse.json();
        console.log(decks); //TODO REMOVE ME 

        // now display the decks in a list, for that we need to append <li> elements to the container
        const deckDiv = document.getElementById("decks-container");
        const deckUl = deckDiv.querySelector("#decks-list");
        const fragment = document.createDocumentFragment();

        decks.forEach(deck => {
            const li = document.createElement("li");
            li.textContent = deck.name;
            fragment.appendChild(li);
        });

        deckUl.appendChild(fragment);
    }catch (error){
        console.log("Error while displaying Decks", error)
    }

    /////////////////////// create a new deck //////////////////////////////
    try {

        // I need to attach an EventListener to the submit event on the form we have (we have only one so it is fine if we just attach it to submit for now)
        const form = document.getElementById("create-deck-form");
        form.addEventListener("submit", async (event) => {
            event.preventDefault(); //stop the page from reloading
            
            const deckName = document.getElementById("deck-name").value;
            const deckDesc = document.getElementById("deck-description").value;
            // call /post endpoint with body 
            const body = {
                "name": deckName,
                "description": deckDesc
            }

            const createDeckResponse = await fetch(
                "/decks", {
                    method: "POST",
                    headers: header,
                    body: JSON.stringify(body)
                }
            )
            if(createDeckResponse.ok){
                // after deck creation immediately append new deck to the current list to avoid having to wait for reload
                const deckDiv = document.getElementById("decks-container");
                const deckUl = deckDiv.querySelector("#decks-list");

                const newDeck = await createDeckResponse.json();
                const li = document.createElement("li");
                li.textContent = newDeck.name;
                deckUl.appendChild(li);

                form.reset();
            }
            });
    }catch (error) {
        console.log("Failed to create Deck", error)
    }

    document.getElementById("logout-link").addEventListener("click", () => {
        localStorage.removeItem("authToken");
    });
});
