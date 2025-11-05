// FAQ Accordion Functionality
document.addEventListener('DOMContentLoaded', function() {
    const faqQuestions = document.querySelectorAll('.faq-question');
    
    faqQuestions.forEach(question => {
        question.addEventListener('click', function() {
            const faqItem = this.closest('.faq-item');
            const answer = faqItem.querySelector('.faq-answer');
            const icon = this.querySelector('i');
            
            // Close all other FAQ items
            document.querySelectorAll('.faq-item').forEach(item => {
                if (item !== faqItem) {
                    const otherAnswer = item.querySelector('.faq-answer');
                    const otherIcon = item.querySelector('.faq-question i');
                    
                    otherAnswer.style.display = 'none';
                    otherIcon.style.transform = 'rotate(0deg)';
                    item.querySelector('.faq-question').style.background = 'rgba(255, 255, 255, 0.05)';
                }
            });
            
            // Toggle current FAQ item
            if (answer.style.display === 'none' || answer.style.display === '') {
                answer.style.display = 'block';
                icon.style.transform = 'rotate(180deg)';
                this.style.background = 'rgba(255, 193, 7, 0.1)';
            } else {
                answer.style.display = 'none';
                icon.style.transform = 'rotate(0deg)';
                this.style.background = 'rgba(255, 255, 255, 0.05)';
            }
        });
    });
}); 