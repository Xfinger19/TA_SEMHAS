// Dashboard real-time updates
document.addEventListener('DOMContentLoaded', function() {
    loadDashboardData();
    loadRecentActivity();
    
    // Refresh data every 10 seconds
    setInterval(() => {
        loadDashboardData();
        loadRecentActivity();
    }, 10000);
});

function loadDashboardData() {
    fetch('/api/dashboard_data')
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                console.error('Error loading dashboard data:', data.error);
                return;
            }

            // Update statistics cards
            if (data.statistics) {
                document.getElementById('total-masuk').textContent = data.statistics.total_masuk || 0;
                document.getElementById('total-keluar').textContent = data.statistics.total_keluar || 0;
                document.getElementById('wajah-didalam').textContent = data.statistics.wajah_di_dalam || 0;
                document.getElementById('unique-faces').textContent = data.statistics.unique_faces || 0;
            }

            // Update today stats
            if (data.today_stats) {
                const todayStats = document.getElementById('today-stats');
                todayStats.innerHTML = `
                    <div class="mb-2">
                        <i class="fas fa-calendar-day me-2"></i>
                        <strong>Total Hari Ini:</strong> ${data.today_stats.total_today || 0}
                    </div>
                    <div class="mb-2">
                        <i class="fas fa-sign-in-alt me-2"></i>
                        <strong>Masuk Hari Ini:</strong> ${data.today_stats.masuk_today || 0}
                    </div>
                    <div class="mb-2">
                        <i class="fas fa-sign-out-alt me-2"></i>
                        <strong>Keluar Hari Ini:</strong> ${data.today_stats.keluar_today || 0}
                    </div>
                `;
            }
        })
        .catch(error => {
            console.error('Error loading dashboard data:', error);
        });
}

function loadRecentActivity() {
    fetch('/api/recent_activity')
        .then(response => response.json())
        .then(data => {
            const container = document.getElementById('recent-activity');
            
            if (data.error) {
                container.innerHTML = '<div class="text-danger">Error loading recent activity</div>';
                return;
            }

            if (data.length === 0) {
                container.innerHTML = '<div class="text-muted">Tidak ada aktivitas terbaru</div>';
                return;
            }

            let html = '';
            data.forEach(activity => {
                const confidencePercent = (activity.confidence * 100).toFixed(1);
                const badgeClass = activity.confidence > 0.8 ? 'bg-success' : 
                                 activity.confidence > 0.5 ? 'bg-warning' : 'bg-danger';
                const statusClass = activity.status_masuk_keluar === 'masuk' ? 'success' : 'warning';
                
                html += `
                <div class="activity-item mb-3 p-3 border rounded">
                    <div class="d-flex justify-content-between align-items-start">
                        <div class="flex-grow-1">
                            <h6 class="mb-1">${activity.nim_nama || 'Tidak Dikenali'}</h6>
                            <small class="text-muted">${activity.waktu} • ${activity.lokasi}</small>
                        </div>
                        <div class="text-end">
                            <span class="badge bg-${statusClass}">${activity.status_masuk_keluar.toUpperCase()}</span>
                            <br>
                            <small class="text-muted">${confidencePercent}%</small>
                        </div>
                    </div>
                </div>
                `;
            });
            
            container.innerHTML = html;
        })
        .catch(error => {
            console.error('Error loading recent activity:', error);
            document.getElementById('recent-activity').innerHTML = '<div class="text-danger">Error loading recent activity</div>';
        });
}