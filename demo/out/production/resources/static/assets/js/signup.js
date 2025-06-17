document.addEventListener("DOMContentLoaded", () => {

    // 이메일 중복체크
    const checkEmailBtn = document.getElementById("checkEmailBtn");
    const emailInput = document.getElementById("email");
    const emailError = document.getElementById("emailError");

    // 초기화 기본갑 false
    let isEmailChecked = false;

    checkEmailBtn.addEventListener("click", async function (e) {
        e.preventDefault();

        const email = emailInput.value.trim();

        // 이메일 유효성 검사
        const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

        if (!emailPattern.test(email)) {
            emailError.textContent = "이메일 형식으로 입력하세요";
            emailError.style.display = "block";
            isEmailChecked = false;
            return;
        }

        try {
            // encodeURIComponent(email)로 인코딩된 문자열을
            // Spring 컨트롤러에서 @RequestParam으로 자동 디코딩
            const response = await fetch(`/check-email?userEmail=${encodeURIComponent(email)}`);
            const isDuplicate = await response.json();

            if (isDuplicate) {
                emailError.textContent = "이미 사용 중인 이메일입니다.";
                emailError.style.color = "red";
                emailError.style.display = "block";
                isEmailChecked = false;
            } else {
                emailError.textContent = "사용 가능한 이메일입니다.";
                emailError.style.color = "green";
                emailError.style.display = "block";
                isEmailChecked = true;
                emailInput.readOnly = true;
            }

        } catch (err) {
            console.error("이메일 중복 확인 실패:", err);
            emailError.textContent = "중복 확인 중 오류가 발생했습니다.";
            emailError.style.color = "red";
            emailError.style.display = "block";
            isEmailChecked = false;
        }

    })


// 1. 회원 가입 이벤트 핸들러 등록
    let submit = document.getElementById("signupForm");

    submit.addEventListener("submit", function (e) {
        e.preventDefault(); // 페이지가 새로고침되는 기본 동작을 막음

        // 이메일 중복확인 여부 체크
        if (!isEmailChecked) {
            alert("이메일 중복 확인을 해주세요.");
            return;  // 중복확인이 안 됐으면 submit 중단
        }

        // 2. 입력값 읽어오기 & 변수 세팅
        const name = document.getElementById("name").value.trim();
        const password = document.getElementById("password").value;
        const confirmPassword = document.getElementById("confirmPassword").value; // 비밀번호 확인

        const location = document.getElementById("user_location").value.trim(); // 소재지
        const employeeCount = document.getElementById("employee_count").value; // 직원수
        const userSales = document.getElementById("user_sales").value; // 매출액
        const userYears = document.getElementById("user_years").value // 회사 업력

        // 에러처리
        const passwordError = document.getElementById("passwordError");

        // 비밀번호 유효성 검사
        if (password !== confirmPassword) {
            passwordError.style.display = "block"; // block 블록레벨 요소를 보이도록 함
            return;
        } else {
            passwordError.style.display = "none";
        }

        // 이메일 중복 체크
        try {

        } catch (err) {
            console.error("중복 체크 실패:", err);
        }


        // back-end 서버에 회원가입 정보 전송
        fetch("/signup", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                userName: name,
                userEmail: emailInput.value,
                userPwd: password,
                userLocation: location,
                userYears: userYears,
                userEmployees: employeeCount,
                userSalesRange: userSales
            }),
        })
            .then((response) => {
                if (!response.ok) {
                    throw new Error("회원가입 실패");
                }
                return response.json();
            })
            .then((data) => {
                alert("회원가입이 완료되었습니다.");
                window.location.href = "/";

            })
            .catch((error) => {
                console.error("회원가입 오류:", error);
            });

    });

});