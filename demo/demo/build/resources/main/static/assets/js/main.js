document.addEventListener("DOMContentLoaded", () => {

    // 로그아웃
    const logoutBtn = document.getElementById("logoutBtn");
    logoutBtn.addEventListener("click", () => {
        // 브라우저에서 /logout GET 요청
        window.location.href = "/logout";
    });


});