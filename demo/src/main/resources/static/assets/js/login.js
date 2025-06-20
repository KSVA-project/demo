document.addEventListener("DOMContentLoaded", () => {

    const form = document.getElementById("loginForm");
    const emailInput = document.getElementById("email");
    const passwordInput = document.getElementById("password");
    const emailError = document.getElementById("emailError");
    const loginError = document.getElementById("loginError");

    form.addEventListener("submit", function (e) {
        e.preventDefault();

        // 1. 이메일 형식 검증
        const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

        if (!emailPattern.test(emailInput.value)) {
            emailError.style.display = "block";
            loginError.style.display = "none";
            return;

        } else {
            emailError.style.display = "none";
        }

        // 2. 로그인 요청 보내기 (JSON 헤더 포함)
        fetch("/login", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                userEmail: emailInput.value,
                userPwd: passwordInput.value,
            }),
        })
            .then((res) => {
                if (!res.ok) throw new Error("서버 에러 발생");
                console.log("응답 상태:", res.status);
                return res.json();
            })
            .then((data) => {
                if (data != null) {
                    // 로그인 성공
                    sessionStorage.setItem("userIdx", data.userIdx);
                    sessionStorage.setItem("userName", data.userName);

                    window.location.href = "/main"; // 원하는 페이지 이동

                } else {
                    // 로그인 실패
                    throw new Error("로그인 실패");
                }
            })
            .catch((err) => {
                console.error("로그인 오류:", err);
                loginError.style.display = "block";
            });

    });
});