function loginError(child, parent, text)
{
    document.addEventListener('DOMContentLoaded', function(){
        document.querySelector(child).setAttribute('class', 'form-control is-invalid');
        const feedback = document.createElement('div');
        feedback.setAttribute('class', 'invalid-feedback text-left');
        feedback.textContent = text;
        document.querySelector(parent).appendChild(feedback);
      });
}