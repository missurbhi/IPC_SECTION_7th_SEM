// JavaScript for handling the multi-step form and submitting data to the server.

// Get references to all form steps and the progress bar
const form = document.getElementById('fir-form');
const steps = document.querySelectorAll('.form-step');
const progressBar = document.getElementById('progress-bar');
const stepLabels = document.querySelectorAll('[id^="step-"]');
const submitButton = document.querySelector('button[type="submit"]'); // Correctly select the submit button
const reviewContent = document.getElementById('review-content');
const predictButton = document.getElementById('predict-ipc-button');
const loadingSpinner = document.getElementById('loading-spinner');
const predictionContainer = document.getElementById('prediction-result-container');
const predictionResultDiv = document.getElementById('prediction-result');

let currentStep = 0;
let predictedIpcSection = 'N/A'; // Store the predicted IPC section

// Custom alert functionality to replace window.alert() and window.confirm()
const customAlert = document.getElementById('custom-alert');
const alertMessage = document.getElementById('alert-message');

function showAlert(message) {
    alertMessage.textContent = message;
    customAlert.classList.remove('hidden');
}

function closeAlert() {
    customAlert.classList.add('hidden');
}

// Function to update the progress bar and step labels
function updateProgress() {
    const progress = (currentStep / (steps.length - 1)) * 100;
    progressBar.style.width = progress + '%';

    // Update the color of the step labels
    stepLabels.forEach((label, index) => {
        if (index <= currentStep) {
            label.classList.add('text-indigo-600');
            label.classList.remove('text-gray-500');
        } else {
            label.classList.remove('text-indigo-600');
            label.classList.add('text-gray-500');
        }
    });
}

// Function to move to the next step
function nextStep() {
    // Basic form validation for the current step
    const currentStepInputs = steps[currentStep].querySelectorAll('input, select, textarea');
    let allValid = true;
    currentStepInputs.forEach(input => {
        if (input.hasAttribute('required') && !input.value) {
            allValid = false;
        }
    });

    if (!allValid) {
        showAlert("Please fill in all the required fields.");
        return;
    }

    if (currentStep < steps.length - 1) {
        steps[currentStep].classList.add('hidden');
        currentStep++;
        steps[currentStep].classList.remove('hidden');
        updateProgress();

        // If we are on the review step, populate the review content
        if (currentStep === steps.length - 1) {
            populateReviewContent();
        }
    }
}

// Function to move to the previous step
function prevStep() {
    if (currentStep > 0) {
        steps[currentStep].classList.add('hidden');
        currentStep--;
        steps[currentStep].classList.remove('hidden');
        updateProgress();
    }
}

// Function to add a new witness input field
function addWitness() {
    const witnessContainer = document.getElementById('witness-container');
    const newWitnessIndex = witnessContainer.children.length + 1;
    const newWitnessDiv = document.createElement('div');
    newWitnessDiv.className = 'bg-gray-100 p-4 rounded-lg flex flex-col space-y-2';
    newWitnessDiv.innerHTML = `
        <label class="block">
            <span class="text-gray-700">Witness ${newWitnessIndex} Name</span>
            <input type="text" class="witness-name mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50 p-2">
        </label>
        <label class="block">
            <span class="text-gray-700">Witness ${newWitnessIndex} Mobile</span>
            <input type="tel" class="witness-mobile mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50 p-2">
        </label>
    `;
    witnessContainer.appendChild(newWitnessDiv);
}

// Function to get all form data and prepare it for submission
function getFormData() {
    const data = {};

    // Complainant details
    data.complainant = {
        name: document.getElementById('complainant-name').value,
        fatherName: document.getElementById('complainant-father-name').value,
        address: document.getElementById('complainant-address').value,
        mobile: document.getElementById('complainant-mobile').value,
        email: document.getElementById('complainant-email').value
    };

    // Incident details
    data.incident = {
        date: document.getElementById('incident-date').value,
        time: document.getElementById('incident-time').value,
        place: document.getElementById('incident-place').value,
        offenceType: document.getElementById('offence-type').value,
        description: document.getElementById('incident-description').value
    };

    // Accused details
    data.accused = {
        name: document.getElementById('accused-name').value,
        address: document.getElementById('accused-address').value,
        description: document.getElementById('accused-description').value
    };

    // Witness details
    data.witnesses = [];
    const witnessNames = document.querySelectorAll('.witness-name');
    const witnessMobiles = document.querySelectorAll('.witness-mobile');
    for (let i = 0; i < witnessNames.length; i++) {
        if (witnessNames[i].value || witnessMobiles[i].value) {
            data.witnesses.push({
                name: witnessNames[i].value,
                mobile: witnessMobiles[i].value
            });
        }
    }
    
    // Add the predicted IPC section to the data
    data.predicted_ipc = predictedIpcSection;

    return data;
}

// Function to populate the review section with collected data
function populateReviewContent() {
    const data = getFormData();
    reviewContent.innerHTML = `
        <div class="space-y-4">
            <div>
                <h3 class="font-bold text-lg text-indigo-700">Complainant Details</h3>
                <p><strong>Name:</strong> ${data.complainant.name}</p>
                <p><strong>Father's Name:</strong> ${data.complainant.fatherName}</p>
                <p><strong>Address:</strong> ${data.complainant.address}</p>
                <p><strong>Mobile:</strong> ${data.complainant.mobile}</p>
                <p><strong>Email:</strong> ${data.complainant.email || 'N/A'}</p>
            </div>
            <hr class="border-gray-300" />
            <div>
                <h3 class="font-bold text-lg text-indigo-700">Incident Details</h3>
                <p><strong>Date & Time:</strong> ${data.incident.date} at ${data.incident.time}</p>
                <p><strong>Place:</strong> ${data.incident.place}</p>
                <p><strong>Offence Type:</strong> ${data.incident.offenceType}</p>
                <p><strong>Description:</strong> ${data.incident.description}</p>
                <p><strong>Predicted IPC Section:</strong> ${data.predicted_ipc}</p>
            </div>
            <hr class="border-gray-300" />
            <div>
                <h3 class="font-bold text-lg text-indigo-700">Accused & Witnesses</h3>
                <p><strong>Accused Name:</strong> ${data.accused.name || 'N/A'}</p>
                <p><strong>Accused Address:</strong> ${data.accused.address || 'N/A'}</p>
                <p><strong>Accused Description:</strong> ${data.accused.description || 'N/A'}</p>
                ${data.witnesses.length > 0 ? `<div class="mt-4">
                    <h4 class="font-semibold text-gray-700">Witnesses:</h4>
                    ${data.witnesses.map(w => `<p><strong>Name:</strong> ${w.name}, <strong>Mobile:</strong> ${w.mobile}</p>`).join('')}
                </div>` : '<p><strong>Witnesses:</strong> None provided</p>'}
            </div>
        </div>
    `;
}

// Event listener for the IPC prediction button
predictButton.addEventListener('click', async () => {
    const description = document.getElementById('incident-description').value;

    if (!description) {
        showAlert("Please describe the incident first to get a prediction.");
        return;
    }

    // Show loading state
    predictButton.disabled = true;
    loadingSpinner.classList.remove('hidden');
    predictionContainer.classList.add('hidden');
    
    try {
        const response = await fetch('http://localhost:8000/predict', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ description: description })
        });
        
        const result = await response.json();

        if (response.ok) {
            predictedIpcSection = result.predicted_ipc_section;
            predictionResultDiv.textContent = predictedIpcSection;
            predictionContainer.classList.remove('hidden');
        } else {
            showAlert(`Prediction Error: ${result.error}`);
            predictedIpcSection = 'N/A';
        }
    } catch (error) {
        console.error('Prediction failed:', error);
        showAlert('An error occurred while predicting. Please try again.');
        predictedIpcSection = 'N/A';
    } finally {
        predictButton.disabled = false;
        loadingSpinner.classList.add('hidden');
    }
});


// Event listener for form submission
form.addEventListener('submit', async (event) => {
    // Prevent the default form submission (page reload)
    event.preventDefault();

    // Disable the submit button and show a loading state
    submitButton.disabled = true;
    submitButton.textContent = 'Submitting...';

    const firData = getFormData();
    
    try {
        // Send the data to your Flask server using the fetch API
        const response = await fetch('http://localhost:8000/submit_fir', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(firData),
        });

        const result = await response.json();

        // Handle the server's response
        if (response.ok) {
            showAlert(result.message);
            // Optional: Reset the form after successful submission
            form.reset();
            currentStep = 0;
            steps.forEach((step, index) => {
                if (index === 0) {
                    step.classList.remove('hidden');
                } else {
                    step.classList.add('hidden');
                }
            });
            updateProgress();
            predictedIpcSection = 'N/A'; // Reset the predicted value
            predictionContainer.classList.add('hidden'); // Hide the prediction result
        } else {
            // Handle HTTP errors or server-side validation errors
            showAlert(`Error: ${result.error}`);
        }
    } catch (error) {
        // Handle network errors or other exceptions
        console.error('Submission failed:', error);
        showAlert('An error occurred. Please try again later.');
    } finally {
        // Re-enable the button regardless of success or failure
        submitButton.disabled = false;
        submitButton.textContent = 'Submit FIR';
    }
});

// Initialize the form state
updateProgress();