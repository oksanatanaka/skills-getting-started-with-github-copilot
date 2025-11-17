document.addEventListener("DOMContentLoaded", () => {
    // Unregister participant from activity
    window.unregisterParticipant = function(activityName, email) {
      if (!confirm(`Remove ${email} from ${activityName}?`)) return;
      fetch(`/activities/${encodeURIComponent(activityName)}/unregister`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email })
      })
        .then(response => {
          if (!response.ok) {
            return response.json().then(data => { throw new Error(data.detail || "Error") });
          }
          return response.json();
        })
        .then(() => {
          // Refresh activities list or UI
          fetchActivities();
        })
        .catch(err => {
          alert("Failed to remove participant: " + err.message);
        });
    }
  const activitiesList = document.getElementById("activities-list");
  const activitySelect = document.getElementById("activity");
  const signupForm = document.getElementById("signup-form");
  const messageDiv = document.getElementById("message");

  // Function to fetch activities from API
  async function fetchActivities() {
    try {
      const response = await fetch("/activities");
      const activities = await response.json();

      // Clear loading message
      activitiesList.innerHTML = "";

      // Populate activities list
      Object.entries(activities).forEach(([name, details]) => {
        const activityCard = document.createElement("div");
        activityCard.className = "activity-card";

        const spotsLeft = details.max_participants - details.participants.length;

        // Participants list HTML
        // Build participants section safely
        let participantsSection = document.createElement("div");
        participantsSection.className = "participants-section";
        const participantsTitle = document.createElement("strong");
        participantsTitle.textContent = "Participants:";
        participantsSection.appendChild(participantsTitle);
        if (details.participants.length > 0) {
          const participantsList = document.createElement("ul");
          participantsList.className = "participants-list";
          participantsList.style.listStyle = "none";
          participantsList.style.paddingLeft = "0";
          details.participants.forEach(p => {
            const li = document.createElement("li");
            li.className = "participant-item";
            const span = document.createElement("span");
            span.textContent = p;
            li.appendChild(span);
            const btn = document.createElement("button");
            btn.className = "delete-participant";
            btn.title = "Remove";
            btn.type = "button";
            btn.style.cursor = "pointer";
            btn.addEventListener("click", () => {
              window.unregisterParticipant(details.name, p);
            });
            const iconSpan = document.createElement("span");
            iconSpan.style.color = "#fff";
            iconSpan.style.fontSize = "0.48em";
            iconSpan.style.cursor = "pointer";
            iconSpan.textContent = "\u{1F5D1}"; // Unicode for 🗑️
            btn.appendChild(iconSpan);
            li.appendChild(btn);
            participantsList.appendChild(li);
          });
          participantsSection.appendChild(participantsList);
        } else {
          const noneP = document.createElement("p");
          noneP.className = "participants-none";
          noneP.textContent = "No participants yet.";
          participantsSection.appendChild(noneP);
        }

        // Build activity card content safely
        const h4 = document.createElement("h4");
        h4.textContent = name;
        activityCard.appendChild(h4);
        const descP = document.createElement("p");
        descP.textContent = details.description;
        activityCard.appendChild(descP);
        const schedP = document.createElement("p");
        const schedStrong = document.createElement("strong");
        schedStrong.textContent = "Schedule:";
        schedP.appendChild(schedStrong);
        schedP.appendChild(document.createTextNode(" " + details.schedule));
        activityCard.appendChild(schedP);
        const availP = document.createElement("p");
        const availStrong = document.createElement("strong");
        availStrong.textContent = "Availability:";
        availP.appendChild(availStrong);
        availP.appendChild(document.createTextNode(` ${spotsLeft} spots left`));
        activityCard.appendChild(availP);
        activityCard.appendChild(participantsSection);

        activitiesList.appendChild(activityCard);

        // Add option to select dropdown
        const option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        activitySelect.appendChild(option);
      });
    } catch (error) {
      activitiesList.innerHTML = "<p>Failed to load activities. Please try again later.</p>";
      console.error("Error fetching activities:", error);
    }
  }

  // Handle form submission
  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = document.getElementById("email").value;
    const activity = document.getElementById("activity").value;

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(activity)}/signup`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email })
        }
      );

      const result = await response.json();

      if (response.ok) {
        messageDiv.textContent = result.message;
        messageDiv.className = "success";
        signupForm.reset();
        fetchActivities();
      } else {
        messageDiv.textContent = result.detail || "An error occurred";
        messageDiv.className = "error";
      }

      messageDiv.classList.remove("hidden");

      // Hide message after 5 seconds
      setTimeout(() => {
        messageDiv.classList.add("hidden");
      }, 5000);
    } catch (error) {
      messageDiv.textContent = "Failed to sign up. Please try again.";
      messageDiv.className = "error";
      messageDiv.classList.remove("hidden");
      console.error("Error signing up:", error);
    }
  });

  // Initialize app
  fetchActivities();
});
