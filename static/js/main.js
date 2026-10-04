// Main JS for SkillTracker Professional SaaS

document.addEventListener('DOMContentLoaded', function() {
    // Auto-dismiss Flash Alerts
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // 1. Student Score Dimension Radar Chart
    const scoreChartCanvas = document.getElementById('scoreBreakdownChart');
    if (scoreChartCanvas) {
        const courseScore = parseFloat(scoreChartCanvas.dataset.courses || 0);
        const projectScore = parseFloat(scoreChartCanvas.dataset.projects || 0);
        const assessScore = parseFloat(scoreChartCanvas.dataset.assessments || 0);
        const certScore = parseFloat(scoreChartCanvas.dataset.certs || 0);
        const mentorScore = parseFloat(scoreChartCanvas.dataset.mentor || 0);

        new Chart(scoreChartCanvas, {
            type: 'radar',
            data: {
                labels: ['Courses (25%)', 'Projects (30%)', 'Assessments (20%)', 'Certificates (10%)', 'Mentor (15%)'],
                datasets: [{
                    label: 'Score Dimension (%)',
                    data: [courseScore, projectScore, assessScore, certScore, mentorScore],
                    backgroundColor: 'rgba(79, 70, 229, 0.2)',
                    borderColor: '#4f46e5',
                    pointBackgroundColor: '#4f46e5'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    r: { suggestedMin: 0, suggestedMax: 100 }
                }
            }
        });
    }

    // 2. Mentor Chart 1: Student Progress Overview
    const mentorProgressCanvas = document.getElementById('mentorStudentProgressChart');
    if (mentorProgressCanvas) {
        const avgScore = parseFloat(mentorProgressCanvas.dataset.avg || 85.0);
        new Chart(mentorProgressCanvas, {
            type: 'bar',
            data: {
                labels: ['W1', 'W2', 'W3', 'W4', 'W5', 'Current'],
                datasets: [{
                    label: 'Avg Progress Score (%)',
                    data: [65, 70, 78, 82, 86, avgScore],
                    backgroundColor: '#4f46e5',
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { y: { suggestedMin: 0, suggestedMax: 100 } }
            }
        });
    }

    // 3. Mentor Chart 2: Skill Development Overview
    const mentorSkillCanvas = document.getElementById('mentorSkillOverviewChart');
    if (mentorSkillCanvas) {
        new Chart(mentorSkillCanvas, {
            type: 'doughnut',
            data: {
                labels: ['Python', 'Flask', 'JavaScript', 'SQL', 'DSA'],
                datasets: [{
                    data: [35, 25, 20, 12, 8],
                    backgroundColor: ['#4f46e5', '#0ea5e9', '#10b981', '#f59e0b', '#6366f1']
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom' } }
            }
        });
    }

    // 4. Mentor Chart 3: Task Completion Rate
    const mentorTaskCanvas = document.getElementById('mentorTaskRateChart');
    if (mentorTaskCanvas) {
        const assigned = parseInt(mentorTaskCanvas.dataset.assigned || 10);
        const completed = parseInt(mentorTaskCanvas.dataset.completed || 7);
        new Chart(mentorTaskCanvas, {
            type: 'pie',
            data: {
                labels: ['Completed', 'Pending / In Progress'],
                datasets: [{
                    data: [completed, Math.max(0, assigned - completed)],
                    backgroundColor: ['#10b981', '#f59e0b']
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom' } }
            }
        });
    }

    // 5. Mentor Chart 4: Course Progress Sync
    const mentorCourseCanvas = document.getElementById('mentorCourseProgressChart');
    if (mentorCourseCanvas) {
        new Chart(mentorCourseCanvas, {
            type: 'bar',
            data: {
                labels: ['Coursera', 'Udemy', 'edX'],
                datasets: [{
                    label: 'Synced Courses %',
                    data: [85, 90, 60],
                    backgroundColor: '#f59e0b',
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { y: { suggestedMin: 0, suggestedMax: 100 } }
            }
        });
    }
});
