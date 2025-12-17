<script>

// 🔔 GLOBAL SUCCESS POPUP FUNCTION
function showSuccessPopup(message) {
    const popup = document.getElementById("successMessage");

    if (!popup) {
        console.error("❌ successMessage popup not found!");
        return;
    }

    // Set message text
    popup.innerText = message;

    // Show popup
    popup.style.display = "block";

    // Hide after 2 sec and refresh page
    setTimeout(() => {
        popup.style.display = "none";
        location.reload();   // 🔄 Refresh UI with updated DB values
    }, 2000);
}



// 🌍 SAVE GLOBAL SETTINGS
function saveGlobal() {
    const minStock = document.getElementById("minStock").value;
    const leadTime = document.getElementById("leadTime").value;

    fetch("/dashboard/reorder/toggle_global", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            min_stock_level: minStock,
            lead_time_days: leadTime
        })
    })
    .then(res => res.json())
    .then(data => {
        // 🎉 Show beautiful popup instead of alert
        showSuccessPopup("Global Settings Updated Successfully!");
    })
    .catch(err => {
        alert("⚠️ Error Updating Settings");
    });
}



// 🟢 PRODUCT ADD POPUP FUNCTION (unchanged)
function addProduct() {
  const successPopup = document.getElementById('successMessage');
  
  if (successPopup) {
    successPopup.style.display = 'block';

    setTimeout(() => {
      successPopup.style.display = 'none';
      document.querySelector("form").reset();
    }, 2000);

  } else {
    console.error("❌ successMessage element not found!");
  }
}

</script>
