package com.example.footballmanagement.controller.mvc.adminsystem;

import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;

import jakarta.servlet.http.HttpServletRequest;

@Controller
public class PaymentAnomalyPageAdminsystemController {

    @GetMapping("/adminsystem/payment-anomalies")
    public String paymentAnomalies(Model model, HttpServletRequest request) {
        model.addAttribute("activePage", "paymentAnomalies");
        model.addAttribute("currentPath", request.getRequestURI());
        return "adminsystem/payment-anomalies";
    }
}
