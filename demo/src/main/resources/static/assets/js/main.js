document.addEventListener("DOMContentLoaded", () => {

    const userIdx = sessionStorage.getItem("userIdx");
    if (!userIdx) {
        // 세션 없는 경우 로그인 페이지로 이동
        window.location.href = "/";
        return;
    }

    // 로그아웃
    const logoutBtn = document.getElementById("logoutBtn");
    logoutBtn.addEventListener("click", () => {
        sessionStorage.clear();  // 클라이언트 측 세션도 정리 (선택)
        window.location.href = "/logout"; // 서버 세션 종료 요청
    });

    // 🔐 뒤로가기 캐시 방지용
    window.addEventListener("pageshow", function (event) {
        if (event.persisted) {
            location.reload();
        }

        const navEntries = performance.getEntriesByType("navigation");
        if (navEntries.length > 0 && navEntries[0].type === "back_forward") {
            location.reload();
        }
    }); //

});
