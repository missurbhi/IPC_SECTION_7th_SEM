document.addEventListener('DOMContentLoaded', () => {
    // Element references
    const loadingMessage = document.getElementById('loading-message');
    const statsContainer = document.getElementById('stats-container');
    const totalCountEl = document.getElementById('total-count');
    const pendingCountEl = document.getElementById('pending-count');
    const acceptedCountEl = document.getElementById('accepted-count');
    const rejectedCountEl = document.getElementById('rejected-count');

    // Chart instances
    let statusPieChart = null;
    let offenceBarChart = null;

    // Fetches data for the summary cards and status chart
    async function fetchStatusData() {
        const apiUrl = 'http://127.0.0.1:8000/police_dashboard_summary';
        try {
            const response = await fetch(apiUrl);
            if (!response.ok) throw new Error(HTTP error! status: ${response.status});
            const data = await response.json();

            // Populate cards
            const total = data.total_complaints || 0;
            const pending = data.pending_complaints || 0;
            const accepted = data.accepted_complaints || 0;
            const rejected = data.rejected_complaints || 0;

            totalCountEl.textContent = total;
            pendingCountEl.textContent = pending;
            acceptedCountEl.textContent = accepted;
            rejectedCountEl.textContent = rejected;

            // Render status chart
            renderStatusChart(total, pending, accepted, rejected);

        } catch (error) {
            console.error('Failed to fetch status data:', error);
            totalCountEl.textContent = 'N/A';
            pendingCountEl.textContent = 'N/A';
            acceptedCountEl.textContent = 'N/A';
            rejectedCountEl.textContent = 'N/A';
            // Display error in the chart area
            const pieChartCanvas = document.getElementById('complaintStatusPieChart');
            if(pieChartCanvas) pieChartCanvas.parentElement.innerHTML = '<p class="text-center text-red-500 py-12">Could not load status data.</p>';
        }
    }

    // Fetches data for the offence type chart
    async function fetchOffenceData() {
        const apiUrl = 'http://127.0.0.1:8000/complaint_offence_summary';
        try {
            const response = await fetch(apiUrl);
            if (!response.ok) throw new Error(HTTP error! status: ${response.status});
            const data = await response.json();
            renderOffenceChart(data);
        } catch (error) {
            console.error('Failed to fetch offence data:', error);
            // Display error in the chart area
            const barChartCanvas = document.getElementById('offenceTypeBarChart');
            if(barChartCanvas) barChartCanvas.parentElement.innerHTML = '<p class="text-center text-red-500 py-12">Could not load offence category data.</p>';
        }
    }

    // Renders the pie chart for complaint statuses
    function renderStatusChart(total, pending, accepted, rejected) {
        const ctx = document.getElementById('complaintStatusPieChart')?.getContext('2d');
        if (!ctx) return;

        if (total === 0) {
            ctx.canvas.parentElement.innerHTML = '<p class="text-center text-gray-500 py-12">No complaint data available.</p>';
            return;
        }

        if (statusPieChart) statusPieChart.destroy();

        statusPieChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Pending', 'Accepted', 'Rejected'],
                datasets: [{
                    label: 'Complaints',
                    data: [pending, accepted, rejected],
                    backgroundColor: ['#f59e0b', '#10b981', '#ef4444'],
                    hoverOffset: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'bottom' },
                    title: { display: true, text: 'Complaint Status Distribution', font: { size: 18 } }
                }
            }
        });
    }

    // Renders the bar chart for offence types
    function renderOffenceChart(data) {
        const ctx = document.getElementById('offenceTypeBarChart')?.getContext('2d');
        if (!ctx) return;

        if (!data || data.length === 0) {
            ctx.canvas.parentElement.innerHTML = '<p class="text-center text-gray-500 py-12">No offence data to categorize.</p>';
            return;
        }

        if (offenceBarChart) offenceBarChart.destroy();
        
        // Sort data to show highest count on top
        data.sort((a, b) => b.count - a.count);

        offenceBarChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.map(item => item.offence_type.replace('_', ' ')),
                datasets: [{
                    label: 'Number of Complaints',
                    data: data.map(item => item.count),
                    backgroundColor: '#4f46e5' // Indigo color
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y', // Horizontal bar chart
                plugins: {
                    legend: { display: false },
                    title: { display: true, text: 'Complaints by Crime Category', font: { size: 18 } }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        ticks: { stepSize: 1 }
                    }
                }
            }
        });
    }

    // Initial data fetch for all components
    async function initializeDashboard() {
        loadingMessage.style.display = 'block';
        statsContainer.style.opacity = '0.5';

        await Promise.all([
            fetchStatusData(),
            fetchOffenceData()
        ]);

        loadingMessage.style.display = 'none';
        statsContainer.style.opacity = '1';
    }

    initializeDashboard();

    // Hamburger menu functionality
    const menuButton = document.getElementById('menu-button-police');
    const navMenu = document.getElementById('nav-menu-police');
    if (menuButton && navMenu) {
        menuButton.addEventListener('click', () => {
            navMenu.classList.toggle('hidden');
            navMenu.classList.toggle('flex');
        });
    }
});