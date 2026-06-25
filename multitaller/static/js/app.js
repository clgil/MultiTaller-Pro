/**
 * MultiTaller - Aplicación JavaScript Moderna
 * Funcionalidades: modo oscuro, sidebar colapsable, animaciones
 * Sin dependencias externas - Vanilla JS
 */

document.addEventListener('DOMContentLoaded', function() {
    
    // ==========================================================================
    // MODO OSCURO
    // ==========================================================================
    
    const themeToggleBtn = document.getElementById('theme-toggle');
    const body = document.body;
    
    // Cargar preferencia guardada en localStorage
    function loadThemePreference() {
        const savedTheme = localStorage.getItem('multitaller-theme');
        if (savedTheme === 'light') {
            body.setAttribute('data-theme', 'light');
            updateThemeIcon(false);
        } else if (savedTheme === 'dark') {
            body.removeAttribute('data-theme');
            updateThemeIcon(true);
        } else {
            // Dark mode por defecto
            body.removeAttribute('data-theme');
            updateThemeIcon(true);
        }
    }
    
    // Actualizar ícono del botón
    function updateThemeIcon(isDark) {
        if (themeToggleBtn) {
            const icon = themeToggleBtn.querySelector('i');
            if (icon) {
                // isDark=true significa modo oscuro activo -> mostrar sol (para cambiar a light)
                // isDark=false significa modo light activo -> mostrar luna (para cambiar a dark)
                icon.className = isDark ? 'bi bi-sun-fill' : 'bi bi-moon-stars-fill';
            }
        }
    }
    
    // Guardar preferencia
    function saveThemePreference(isDark) {
        localStorage.setItem('multitaller-theme', isDark ? 'dark' : 'light');
    }
    
    // Toggle del tema
    if (themeToggleBtn) {
        themeToggleBtn.addEventListener('click', function() {
            const isDark = !body.hasAttribute('data-theme');
            
            if (isDark) {
                body.setAttribute('data-theme', 'light');
                updateThemeIcon(false);
                saveThemePreference(false);
            } else {
                body.removeAttribute('data-theme');
                updateThemeIcon(true);
                saveThemePreference(true);
            }
            
            // Animación sutil de transición
            body.style.transition = 'background-color 0.3s ease, color 0.3s ease';
        });
    }
    
    // Escuchar cambios en la preferencia del sistema
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function(e) {
        if (!localStorage.getItem('multitaller-theme')) {
            if (e.matches) {
                body.removeAttribute('data-theme');
                updateThemeIcon(true);
            } else {
                body.removeAttribute('data-theme');
                updateThemeIcon(true);
            }
        }
    });
    
    // Cargar preferencia al iniciar
    loadThemePreference();
    
    // ==========================================================================
    // SIDEBAR COLAPSABLE
    // ==========================================================================
    
    const menuToggleBtn = document.getElementById('menu-toggle');
    const wrapper = document.getElementById('wrapper');
    const sidebar = document.getElementById('sidebar-wrapper');
    
    // Toggle del menú
    function toggleSidebar() {
        if (window.innerWidth <= 768) {
            // En móviles, mostrar/ocultar completamente
            if (sidebar) {
                sidebar.classList.toggle('open');
            }
        } else {
            // En escritorio, alternar modo mini
            if (wrapper) {
                wrapper.classList.toggle('sidebar-mini');
            }
            
            // Guardar estado en localStorage
            const isMini = wrapper && wrapper.classList.contains('sidebar-mini');
            localStorage.setItem('multitaller-sidebar-mini', isMini ? 'true' : 'false');
        }
    }
    
    if (menuToggleBtn) {
        menuToggleBtn.addEventListener('click', function(e) {
            e.preventDefault();
            toggleSidebar();
        });
    }
    
    // Cargar estado del sidebar guardado
    const savedSidebarState = localStorage.getItem('multitaller-sidebar-mini');
    if (savedSidebarState === 'true' && window.innerWidth > 768 && wrapper) {
        wrapper.classList.add('sidebar-mini');
    }
    
    // Cerrar sidebar al hacer clic fuera en móviles
    document.addEventListener('click', function(e) {
        if (window.innerWidth <= 768 && sidebar && sidebar.classList.contains('open')) {
            if (!sidebar.contains(e.target) && !menuToggleBtn.contains(e.target)) {
                sidebar.classList.remove('open');
            }
        }
    });
    
    // ==========================================================================
    // ANIMACIONES DE ENTRADA
    // ==========================================================================
    
    // Animar tarjetas del dashboard
    const summaryCards = document.querySelectorAll('.summary-card');
    summaryCards.forEach((card, index) => {
        card.classList.add('animate-fade-in-up');
        card.style.animationDelay = `${index * 0.1}s`;
    });
    
    // Animar otras tarjetas
    const cards = document.querySelectorAll('.card');
    cards.forEach((card, index) => {
        if (!card.classList.contains('summary-card')) {
            card.classList.add('animate-fade-in-up');
            card.style.animationDelay = `${0.3 + index * 0.1}s`;
        }
    });
    
    // ==========================================================================
    // CONFIRMACIÓN PARA ACCIONES DESTRUCTIVAS
    // ==========================================================================
    
    const deleteLinks = document.querySelectorAll('a[href*="eliminar"], button[name*="eliminar"]');
    deleteLinks.forEach(function(element) {
        element.addEventListener('click', function(e) {
            const confirmed = confirm('¿Está seguro de que desea eliminar este registro? Esta acción no se puede deshacer.');
            if (!confirmed) {
                e.preventDefault();
                e.stopPropagation();
            }
        });
    });
    
    // ==========================================================================
    // AUTO-CERRAR ALERTAS
    // ==========================================================================
    
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
    
    // ==========================================================================
    // VALIDACIÓN DE FORMULARIOS
    // ==========================================================================
    
    const forms = document.querySelectorAll('form.needs-validation');
    forms.forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });
    
    // ==========================================================================
    // BÚSQUEDA EN TIEMPO REAL CON DEBOUNCE
    // ==========================================================================
    
    const searchInputs = document.querySelectorAll('input[data-search-target]');
    searchInputs.forEach(function(input) {
        let timeout;
        input.addEventListener('keyup', function() {
            clearTimeout(timeout);
            timeout = setTimeout(function() {
                const target = input.getAttribute('data-search-target');
                const value = input.value;
                
                // Filtrar filas de la tabla
                const rows = document.querySelectorAll(target + ' tbody tr');
                rows.forEach(function(row) {
                    const text = row.textContent.toLowerCase();
                    row.style.display = text.includes(value.toLowerCase()) ? '' : 'none';
                });
            }, 300);
        });
    });
    
    // ==========================================================================
    // SELECCIÓN DE TODOS LOS CHECKBOXES
    // ==========================================================================
    
    const selectAllCheckbox = document.getElementById('select-all');
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            const checkboxes = document.querySelectorAll('.item-checkbox');
            checkboxes.forEach(function(cb) {
                cb.checked = selectAllCheckbox.checked;
            });
        });
    }
    
    // ==========================================================================
    // CONFIRMACIÓN DE CONTRASEÑAS
    // ==========================================================================
    
    const passwordConfirm = document.getElementById('password_confirm');
    const passwordInput = document.getElementById('password');
    
    if (passwordConfirm && passwordInput) {
        passwordConfirm.addEventListener('input', function() {
            if (passwordInput.value !== passwordConfirm.value) {
                passwordConfirm.setCustomValidity('Las contraseñas no coinciden');
            } else {
                passwordConfirm.setCustomValidity('');
            }
        });
    }
    
    // ==========================================================================
    // FORMATO DE MONEDA
    // ==========================================================================
    
    const currencyInputs = document.querySelectorAll('input[type="number"][data-currency]');
    currencyInputs.forEach(function(input) {
        input.addEventListener('blur', function() {
            const value = parseFloat(input.value);
            if (!isNaN(value)) {
                input.value = value.toFixed(2);
            }
        });
    });
    
    // ==========================================================================
    // CÁLCULO DE TOTALES EN FORMULARIOS
    // ==========================================================================
    
    const cantidadInputs = document.querySelectorAll('input[name*="cantidad"]');
    const precioInputs = document.querySelectorAll('input[name*="precio"]');
    
    [cantidadInputs, precioInputs].forEach(function(inputs) {
        inputs.forEach(function(input) {
            input.addEventListener('change', calculateTotals);
        });
    });
    
    function calculateTotals() {
        const cantidades = document.querySelectorAll('input[name*="cantidad"]');
        const precios = document.querySelectorAll('input[name*="precio"]');
        let total = 0;
        
        cantidades.forEach(function(cantidad, index) {
            const qty = parseFloat(cantidad.value) || 0;
            const price = parseFloat(precios[index]?.value) || 0;
            total += qty * price;
        });
        
        const totalDisplay = document.getElementById('total-calculado');
        if (totalDisplay) {
            totalDisplay.textContent = total.toFixed(2);
        }
    }
    
    // ==========================================================================
    // TOOLTIP DE BOOTSTRAP (inicialización automática)
    // ==========================================================================
    
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // ==========================================================================
    // POPOVER DE BOOTSTRAP (inicialización automática)
    // ==========================================================================
    
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // ==========================================================================
    // SISTEMA DE NOTIFICACIONES
    // ==========================================================================
    
    const notificationBtn = document.getElementById('btn-notificaciones');
    
    if (notificationBtn) {
        // Cargar notificaciones al hacer clic en el botón
        notificationBtn.addEventListener('click', function() {
            cargarNotificacionesDropdown();
        });
        
        // Auto-actualizar cada 30 segundos
        setInterval(cargarNotificacionesDropdown, 30000);
    }
    
    function cargarNotificacionesDropdown() {
        fetch('/api/notificaciones/list')
            .then(response => response.json())
            .then(data => {
                const container = document.getElementById('notification-dropdown-list');
                const badge = document.querySelector('.notification-badge');
                
                // Actualizar badge
                if (badge) {
                    if (data.total > 0) {
                        badge.textContent = data.total > 9 ? '9+' : data.total;
                        badge.style.display = 'flex';
                    } else {
                        badge.style.display = 'none';
                    }
                }
                
                // Renderizar lista
                if (data.notificaciones && data.notificaciones.length > 0) {
                    let html = '';
                    data.notificaciones.forEach(notif => {
                        const iconClass = getNotificationIcon(notif.tipo);
                        const colorClass = getNotificationColor(notif.tipo);
                        
                        html += `
                            <div class="p-3 border-bottom notification-item-hover" style="cursor: pointer;" onclick="${notif.enlace ? "window.location.href='"+notif.enlace+"'" : 'marcarLeidaFromDropdown('+notif.id+')'}">
                                <div class="d-flex align-items-start">
                                    <i class="bi ${iconClass} ${colorClass} me-2 fs-5"></i>
                                    <div class="flex-grow-1">
                                        <h6 class="mb-1 small fw-semibold">${notif.titulo}</h6>
                                        <p class="mb-1 small text-muted">${notif.mensaje.substring(0, 80)}${notif.mensaje.length > 80 ? '...' : ''}</p>
                                        <small class="text-muted" style="font-size: 0.7rem;">${notif.fecha_creacion}</small>
                                    </div>
                                </div>
                            </div>
                        `;
                    });
                    container.innerHTML = html;
                } else {
                    container.innerHTML = `
                        <div class="text-center py-4 text-muted">
                            <i class="bi bi-bell-slash fs-3"></i>
                            <p class="mb-0 mt-2 small">No hay notificaciones nuevas</p>
                        </div>
                    `;
                }
            })
            .catch(error => {
                console.error('Error cargando notificaciones:', error);
            });
    }
    
    function getNotificationIcon(tipo) {
        switch(tipo) {
            case 'danger': return 'bi-exclamation-triangle-fill';
            case 'warning': return 'bi-exclamation-circle-fill';
            case 'success': return 'bi-check-circle-fill';
            default: return 'bi-info-circle-fill';
        }
    }
    
    function getNotificationColor(tipo) {
        switch(tipo) {
            case 'danger': return 'text-danger';
            case 'warning': return 'text-warning';
            case 'success': return 'text-success';
            default: return 'text-primary';
        }
    }
    
    function marcarLeidaFromDropdown(id) {
        fetch(`/notificaciones/marcar_leida/${id}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                cargarNotificacionesDropdown();
            }
        });
    }

});

// ==========================================================================
// FUNCIONES GLOBALES
// ==========================================================================

/**
 * Imprimir orden/recibo
 */
function imprimirOrden(ordenId) {
    window.open('/orden/' + ordenId + '/imprimir', '_blank');
}

/**
 * Exportar tabla a CSV
 */
function exportTableToCSV(tableSelector, filename) {
    const table = document.querySelector(tableSelector);
    if (!table) return;
    
    let csv = [];
    const rows = table.querySelectorAll('tr');
    
    rows.forEach(function(row) {
        const cols = row.querySelectorAll('td, th');
        const rowData = [];
        cols.forEach(function(col) {
            rowData.push('"' + col.textContent.trim().replace(/"/g, '""') + '"');
        });
        csv.push(rowData.join(','));
    });
    
    downloadCSV(csv.join('\n'), filename);
}

/**
 * Descargar archivo CSV
 */
function downloadCSV(csv, filename) {
    const csvFile = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const downloadLink = document.createElement('a');
    downloadLink.download = filename;
    downloadLink.href = window.URL.createObjectURL(csvFile);
    downloadLink.style.display = 'none';
    document.body.appendChild(downloadLink);
    downloadLink.click();
    document.body.removeChild(downloadLink);
}

/**
 * Mostrar/ocultar contraseña
 */
function togglePassword(inputId, button) {
    const input = document.getElementById(inputId);
    if (input.type === 'password') {
        input.type = 'text';
        button.textContent = 'Ocultar';
        if (button.querySelector('i')) {
            button.querySelector('i').className = 'bi bi-eye-slash-fill';
        }
    } else {
        input.type = 'password';
        button.textContent = 'Mostrar';
        if (button.querySelector('i')) {
            button.querySelector('i').className = 'bi bi-eye-fill';
        }
    }
}

/**
 * Formatear número como moneda
 */
function formatCurrency(amount, currency = '$') {
    return currency + ' ' + parseFloat(amount).toFixed(2).replace(/\d(?=(\d{3})+\.)/g, '$&,');
}

/**
 * Mostrar notificación toast (si existe el componente)
 */
function showToast(message, type = 'info') {
    const toastContainer = document.getElementById('toast-container');
    if (!toastContainer) return;
    
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${message}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    toast.addEventListener('hidden.bs.toast', function() {
        toast.remove();
    });
}
