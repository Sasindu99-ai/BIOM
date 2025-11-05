document.addEventListener('DOMContentLoaded', function () {
    window.animatePills = () => {
        const animatedPill = document.querySelector('.animated-pill');
        const navItems = animatedPill.querySelectorAll('.nav-item');
        const activeBg = document.querySelector('.animated-pill-active');
        const activeBtn = animatedPill.querySelector('.nav-link.active');

        function moveActiveBg(button) {
            const btnRect = button.getBoundingClientRect();
            const navRect = button.closest('.nav').getBoundingClientRect();
            const firstElement = button.closest('.nav').children[0].getBoundingClientRect()
            activeBg.style.width = `${btnRect.width}px`;
            activeBg.style.height = `${btnRect.height}px`;
            activeBg.style.transform = `translate(${btnRect.x - firstElement.x}px, ${btnRect.top - navRect.top}px)`;
        }

        moveActiveBg(activeBtn);
        navItems.forEach(item => {
            item.addEventListener('click', function (event) {
                navItems.forEach(navItem => navItem.querySelector('.nav-link').classList.remove('active'));
                const button = event.currentTarget.querySelector('.nav-link');
                button.classList.add('active');
                moveActiveBg(button);
            });
        });

        window.addEventListener('resize', function () {
            moveActiveBg(animatedPill.querySelector('.nav-link.active'));
        });
    }
});
