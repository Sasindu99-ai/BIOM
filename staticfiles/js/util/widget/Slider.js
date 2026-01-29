export default class Slider {
    id;
    prevButton;
    nextButton;
    slider;
    scrollView;
    slides;
    manual = true;

    async init() {
        this.slider = document.getElementById(this.id);
        this.scrollView = this.slider.getElementsByClassName("slider-scroll-view")[0];
        this.slides = this.slider.getElementsByClassName("slider-slide");

        this.prevButton = this.slider.getElementsByClassName("carousel-control-prev")[0];
        this.nextButton = this.slider.getElementsByClassName("carousel-control-next")[0];

        this.prevButton.addEventListener("click", () => {
            this.prev();
        });
        this.nextButton.addEventListener("click", () => {
            this.next();
        });
    }

    next() {
        if (!this.manual) this.scrollView.style.overflowX = "auto !important";
        if (this.scrollView.scrollLeft < this.scrollView.scrollWidth - this.scrollView.offsetWidth) {
            this.scrollView.scrollLeft += this.slides[0].offsetWidth;
        }
        if (!this.manual) this.scrollView.style.overflowX = "hidden";
    }

    prev() {
        if (!this.manual) this.scrollView.style.overflowX = "auto !important";
        if (this.scrollView.scrollLeft > 0) {
            this.scrollView.scrollLeft -= this.slides[0].offsetWidth;
        }
        if (!this.manual) this.scrollView.style.overflowX = "hidden";
    }

    constructor(id=null) {
        if (id != null) {
            this.id = id;
            this.init();
        }
    }
}