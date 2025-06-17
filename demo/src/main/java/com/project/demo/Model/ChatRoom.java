package com.project.demo.Model;

import jakarta.persistence.*;
import lombok.*;

import java.time.LocalDateTime;
import java.util.List;

@Entity
@Table(name="tb_chatroom")
@NoArgsConstructor
@AllArgsConstructor
@Getter
@Setter
public class ChatRoom {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "croom_idx")
    private Integer croomIdx; // 채팅방 식별자

    @Column(name = "user_idx", nullable = false)
    private Integer userIdx; // 사용자 식별자 (외래키 제거, 정수로 직접 저장)

    @Column(name = "croom_title", nullable = false, length = 50)
    private String croomTitle = "새 채팅"; // 채팅방 제목 (기본값)

    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt = LocalDateTime.now(); // 개설 시간
}
