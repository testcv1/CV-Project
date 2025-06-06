document.addEventListener('DOMContentLoaded', function() {
  // Toggle password visibility for all password fields
  document.querySelectorAll('.toggle-password').forEach(function(icon) {
    icon.addEventListener('click', function() {
      const passwordInput = this.closest('.input-group').querySelector('input');
      const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
      passwordInput.setAttribute('type', type);
      this.classList.toggle('fa-eye-slash');
    });
  });

  // Add animation to form elements
  const authCard = document.querySelector('.auth-card');
  if (authCard) {
    setTimeout(() => {
      authCard.style.opacity = '1';
      authCard.style.transform = 'translateY(0)';
    }, 100);
  }
});