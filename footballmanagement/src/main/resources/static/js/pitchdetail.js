async function loadPitchDetail() {
    const container = document.getElementById("pitchDetailContainer");

    container.innerHTML = `<p>${i18n.loading}</p>`;

    try {
        const res = await fetch(`/api/pitches/${pitchId}`);
        if (!res.ok) {
            container.innerHTML = `<p>${i18n.error}</p>`;
            return;
        }
        const p = await res.json();

        const coverRes = await fetch(`/api/pitches/${pitchId}/images/cover`);
        let coverUrl = "/images/default-cover.jpg";
        if (coverRes.ok) {
            const cover = await coverRes.json();
            if (cover && cover.url) {
                coverUrl = cover.url;
            }
        }

        const coverSrc = sanitizeResourceUrl(coverUrl, "/images/default-cover.jpg");

        container.innerHTML = `
            <div class="pitch-detail-card">
                <img src="${escapeHtmlAttr(coverSrc)}" alt="Pitch Cover" class="pitch-detail-img">

                <div class="pitch-detail-info">
                    <h3>${escapeHtml(p.name)}</h3>
                    <p><strong>${escapeHtml(i18n.location)}</strong> ${escapeHtml(p.location)}</p>
                    <p><strong>${escapeHtml(i18n.description)}</strong> ${escapeHtml(p.description || "-")}</p>
                    <p><strong>${escapeHtml(i18n.branch)}</strong> ${escapeHtml(p.branchName)}</p>
                    <p><strong>${escapeHtml(i18n.type)}</strong> ${escapeHtml(p.pitchTypeName)}</p>
                    <p><strong>${i18n.status}</strong> ${p.active ? i18n.active : i18n.inactive}</p>
                    <a href="#" id="bookingBtn" class="booking-btn">${i18n.booking}</a>
                </div>
            </div>
        `;

        const galleryRes = await fetch(`/api/pitches/${pitchId}/images/gallery`);
        if (galleryRes.ok) {
            const gallery = await galleryRes.json();
            const galleryContainer = document.getElementById("galleryImages");
            galleryContainer.innerHTML = "";

            gallery.forEach(img => {
                const el = document.createElement("img");
                el.src = sanitizeResourceUrl(img.url, "/images/default-cover.jpg");
                galleryContainer.appendChild(el);
            });

            const prevBtn = document.getElementById("galleryPrev");
            const nextBtn = document.getElementById("galleryNext");
            const scrollAmount = 200;

            prevBtn.addEventListener("click", () => {
                galleryContainer.scrollBy({ left: -scrollAmount, behavior: "smooth" });
            });

            nextBtn.addEventListener("click", () => {
                galleryContainer.scrollBy({ left: scrollAmount, behavior: "smooth" });
            });
        }

        await loadAverageRating();
        await loadReviews();
        await setupReviewForm();

    } catch (err) {
        console.error("Error:", err);
        container.innerHTML = `<p>${i18n.fetchFailed}</p>`;
    }
}

async function loadAverageRating() {
    const avgRes = await fetch(`/api/pitches/${pitchId}/reviews/average`);
    if (!avgRes.ok) return;

    const avg = await avgRes.json();

    const stars = Array.from({ length: 5 }, (_, i) => {
        return `<span class="star ${i < Math.round(avg) ? "filled" : ""}">&#9733;</span>`;
    }).join("");

    document.getElementById("avgRating").innerHTML = `${avg} ${stars}`;
}

async function loadReviews() {
    const reviewsRes = await fetch(`/api/pitches/${pitchId}/reviews`);
    if (!reviewsRes.ok) return;

    const reviews = await reviewsRes.json();
    const reviewContainer = document.getElementById("reviewsContainer");
    reviewContainer.innerHTML = "";

    if (reviews.length === 0) {
        reviewContainer.innerHTML = `<p>${i18n.reviewNone}</p>`;
        return;
    }

    reviews.forEach(r => {
        const card = document.createElement("div");
        card.classList.add("review-card");

        const userName = document.createElement("strong");
        userName.textContent = r.userFullName || "";

        const stars = document.createElement("div");
        stars.className = "review-stars";
        for (let i = 0; i < 5; i++) {
            const star = document.createElement("span");
            star.classList.add("star");
            if (i < Number(r.rating || 0)) {
                star.classList.add("filled");
            }
            star.textContent = "\u2605";
            stars.appendChild(star);
        }

        const content = document.createElement("p");
        content.textContent = r.content || "";

        card.append(userName, stars, content);

        reviewContainer.appendChild(card);
    });
}

function renderRatingStars(current = 5) {
    const container = document.getElementById("ratingStars");
    const ratingInput = document.getElementById("ratingValue");

    if (!container || !ratingInput) return;

    container.innerHTML = "";

    for (let i = 1; i <= 5; i++) {
        const star = document.createElement("span");
        star.classList.add("star");
        if (i <= current) {
            star.classList.add("filled");
        }
        star.textContent = "\u2605";

        star.addEventListener("mouseenter", () => {
            paintRatingStars(i);
        });

        star.addEventListener("click", () => {
            ratingInput.value = i;
            paintRatingStars(i);
        });

        container.appendChild(star);
    }

    container.onmouseleave = () => {
        paintRatingStars(Number(ratingInput.value));
    };
}

function paintRatingStars(value) {
    const stars = document.querySelectorAll("#ratingStars .star");
    stars.forEach((star, index) => {
        if (index < value) {
            star.classList.add("filled");
        } else {
            star.classList.remove("filled");
        }
    });
}

async function setupReviewForm() {
    const reviewForm = document.getElementById("reviewForm");
    const reviewAuthMessage = document.getElementById("reviewAuthMessage");
    const ratingValue = document.getElementById("ratingValue");
    const reviewContent = document.getElementById("reviewContent");

    let currentUser;
    try {
        const meRes = await fetch("/api/user/me");
        if (!meRes.ok) {
            reviewForm.style.display = "none";
            reviewAuthMessage.innerHTML = `<a href="/login">${i18n.reviewLoginRequired}</a>`;
            return;
        }
        currentUser = await meRes.json();
    } catch (err) {
        reviewForm.style.display = "none";
        reviewAuthMessage.innerHTML = `<a href="/login">${i18n.reviewLoginRequired}</a>`;
        return;
    }

    if (!currentUser || currentUser.role !== "USER") {
        reviewForm.style.display = "none";
        reviewAuthMessage.textContent = i18n.reviewUserOnly;
        return;
    }

    reviewForm.style.display = "block";
    reviewAuthMessage.innerHTML = "";

    ratingValue.value = 5;
    renderRatingStars(5);

    try {
        const reviewsRes = await fetch(`/api/pitches/${pitchId}/reviews`);
        if (reviewsRes.ok) {
            const reviews = await reviewsRes.json();
            const myReview = reviews.find(r => r.userId === currentUser.id);
            if (myReview) {
                ratingValue.value = myReview.rating;
                reviewContent.value = myReview.content || "";
                renderRatingStars(myReview.rating);
            }
        }
    } catch (err) {
        console.error("Load my review error:", err);
    }

    reviewForm.addEventListener("submit", async function (e) {
        e.preventDefault();

        const rating = Number(ratingValue.value);
        const content = reviewContent.value.trim();

        try {
            const res = await fetch(`/api/pitches/${pitchId}/reviews`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ rating, content })
            });

            if (!res.ok) {
                const errorText = await res.text();
                alert(errorText || i18n.reviewSubmitFailed);
                return;
            }

            await loadAverageRating();
            await loadReviews();
        } catch (err) {
            console.error("Submit review error:", err);
            alert(i18n.reviewSubmitError);
        }
    }, { once: true });
}

document.addEventListener("click", async (e) => {
    const btn = e.target.closest("#bookingBtn");
    if (!btn) return;

    e.preventDefault();
    const meRes = await fetch("/api/user/me");
    if (!meRes.ok) {
        alert("Ban can dang nhap de dat lich");
        window.location.href = "/login";
        return;
    }

    const currentUser = await meRes.json();
    if (!currentUser || currentUser.role !== "USER") {
        alert("Ban can dang nhap de dat lich");
        return;
    }

    window.location.href = `/user/booking/${pitchId}`;
});
document.addEventListener("DOMContentLoaded", loadPitchDetail);

function escapeHtml(value) {
    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#39;");
}

function escapeHtmlAttr(value) {
    return escapeHtml(value);
}

function sanitizeResourceUrl(value, fallback) {
    const url = String(value || "").trim();
    if (/^(https?:\/\/|\/)/i.test(url)) {
        return url;
    }
    return fallback;
}

