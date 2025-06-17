package com.project.demo.Model;


import jakarta.persistence.*;
import lombok.*;

import java.time.LocalDateTime;
import java.util.List;

@Entity
@Table(name = "tb_user")
@NoArgsConstructor
@AllArgsConstructor
@Getter
@Setter
public class User {

     @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "user_idx")
    private Integer userIdx;

    @Column(name = "user_email", nullable = false, length = 50)
    private String userEmail;

    @Column(name = "user_pwd", nullable = false, length = 50)
    private String userPwd;

    @Column(name = "user_name", nullable = false, length = 200)
    private String userName; // 기업명

    @Column(name = "user_years", length = 10)
    private String userYears; // 업력

    @Column(name = "user_location", length = 50)
    private String userLocation; // 소재지 (예: 서울, 인천)

    @Column(name = "user_employees", length = 30)
    private String userEmployees; // 직원 수

    @Column(name = "user_sales_range", length = 30)
    private String userSalesRange; // 연매출 범위 문자열 (예: "5~10억")

    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt = LocalDateTime.now();

}
