package com.project.demo.Model;
import jakarta.persistence.*;
import lombok.*;

import java.time.LocalDateTime;

@Entity
@Table(name="tb_chat")
@NoArgsConstructor
@AllArgsConstructor
@Getter
@Setter
public class Chat {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "chat_idx")
    private Integer chatIdx; // 채팅 식별자

    @Column(name = "croom_idx", nullable = false)
    private Integer croomIdx; // 채팅방 식별자

    @Column(name = "chatter", nullable = false, length = 20)
    private String chatter; // 발화자 (예: 'bot' 또는 'user_idx')

    @Column(name = "chat", columnDefinition = "TEXT")
    private String chat; // 채팅 내용

    @Column(name = "ratings", length = 1)
    private String ratings = "1"; // 채팅 평가 점수 (기본값 1)

    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt = LocalDateTime.now(); // 채팅 시간
}
