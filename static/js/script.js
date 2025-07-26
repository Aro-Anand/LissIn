document.addEventListener("DOMContentLoaded", function () {
    const callBtn = document.getElementById("callBtn");
    const formContainer = document.getElementById("formContainer");
    const closeBtn = document.getElementById("closeBtn");
    const callForm = document.getElementById("callForm");
    const serviceChips = document.querySelectorAll(".service-chip");
    const serviceTypeInput = document.getElementById("serviceType");

    // Toggle form visibility
    callBtn.addEventListener("click", () => {
        formContainer.classList.add("active");
    });

    closeBtn.addEventListener("click", () => {
        formContainer.classList.remove("active");
    });

    // Service chip selection
    serviceChips.forEach(chip => {
        chip.addEventListener("click", () => {
            // Remove selected class from all chips
            serviceChips.forEach(c => c.classList.remove("selected"));
            // Add selected class to clicked chip
            chip.classList.add("selected");
            // Update hidden input
            serviceTypeInput.value = chip.dataset.service;
        });
    });

    // Close form when clicking outside
    document.addEventListener("click", (e) => {
        if (!formContainer.contains(e.target) && !callBtn.contains(e.target)) {
            formContainer.classList.remove("active");
        }
    });

    // Form submission
    callForm.addEventListener("submit", function (e) {
        e.preventDefault();

        const submitButton = this.querySelector('button[type="submit"]');
        const originalContent = submitButton.innerHTML;

        submitButton.disabled = true;
        submitButton.innerHTML = '<div class="spinner-border" role="status" aria-hidden="true"></div> Processing...';

        const formData = new FormData(this);

        // Combine country code and phone number
        const countryCode = document.getElementById("countryCode").value;
        const phoneNumber = document.getElementById("phone").value;
        const fullPhoneNumber = countryCode + phoneNumber;
        formData.set("phone", fullPhoneNumber);

        // Simulate form submission (replace with actual endpoint)
        setTimeout(() => {
            const responseDiv = document.getElementById("responseMessage");

            // Simulate success response
            responseDiv.className = "alert alert-success show";
            responseDiv.innerHTML = `<strong>Success!</strong> Your call request has been submitted. We'll contact you shortly!`;
            callForm.reset();

            // Clear service chip selections
            serviceChips.forEach(c => c.classList.remove("selected"));
            serviceTypeInput.value = "";

            // Auto close form after success
            setTimeout(() => {
                formContainer.classList.remove("active");
                responseDiv.classList.remove("show");
            }, 3000);

            submitButton.disabled = false;
            submitButton.innerHTML = originalContent;
        }, 2000);

        // Uncomment below for actual form submission

        fetch("/submit", {
            method: "POST",
            body: formData,
        })
            .then((response) => response.json())
            .then((data) => {
                const responseDiv = document.getElementById("responseMessage");

                if (data.success) {
                    responseDiv.className = "alert alert-success show";
                    responseDiv.innerHTML = `<strong>Success!</strong> ${data.message}`;
                    callForm.reset();
                    serviceChips.forEach(c => c.classList.remove("selected"));
                    serviceTypeInput.value = "";

                    setTimeout(() => {
                        formContainer.classList.remove("active");
                    }, 3000);
                } else {
                    responseDiv.className = "alert alert-danger show";
                    responseDiv.innerHTML = `<strong>Error!</strong> ${data.message}`;
                }

                submitButton.disabled = false;
                submitButton.innerHTML = originalContent;
            })
            .catch((error) => {
                console.error("Error:", error);
                const responseDiv = document.getElementById("responseMessage");
                responseDiv.className = "alert alert-danger show";
                responseDiv.innerHTML = "<strong>Error!</strong> Something went wrong. Please try again later.";

                submitButton.disabled = false;
                submitButton.innerHTML = originalContent;
            });

    });
});
