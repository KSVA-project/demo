document.addEventListener("DOMContentLoaded", () => {


    // ✅ [1] Flatpickr: 설립일 → 업력 자동계산
    flatpickr("#start_date", {
        locale: "ko",  // 한글화
        dateFormat: "Y-m",
        altInput: true,
        altFormat: "Y년 m월",
        plugins: [
            new monthSelectPlugin({
                shorthand: false,
                dateFormat: "Y-m",
                altFormat: "Y년 m월"
            })
        ],
        onChange: function (selectedDates, dateStr) { // 사용자가 날짜를 선택하면 실행

            const [year, month] = dateStr.split('-').map(Number);

            // JavaScript의 Date 객체는 월(month)이 0부터 시작
            const startDate = new Date(year, month - 1);
            const today = new Date();

            let years = today.getFullYear() - startDate.getFullYear();
            if (today.getMonth() < startDate.getMonth()) years--; // 월 단위 보정:

            document.getElementById("user_years").value = years >= 0 ? years : 0;
        }
    });

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


// [3] 회원 가입 제출 이벤트
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

        const userIndustry = document.getElementById("user_industry").value;

        // 체크된 기업 유형들 수집
        const typeNodes = document.querySelectorAll('input[name="user_type"]:checked');
        const userTypes = Array.from(typeNodes).map(input => input.value);

        // 에러처리
        const passwordError = document.getElementById("passwordError");

        // 비밀번호 유효성 검사
        if (password !== confirmPassword) {
            passwordError.style.display = "block"; // block 블록레벨 요소를 보이도록 함
            return;
        } else {
            passwordError.style.display = "none";
        }

        // 설립일 입력 안 했을 경우 대비 (업력 계산 안됨)
        if (!userYears) {
            alert("설립일을 선택하여 업력을 계산해주세요.");
            return;
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
                userSalesRange: userSales,
                userIndustry: userIndustry,
                userTypes: userTypes
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