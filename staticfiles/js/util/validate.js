export default class Validate {
    constructor() {
        let validateFunc = {
            "number": this.inputNumber,
            "name": this.inputName,
            "gmail": this.inputGmail,
            "email": this.inputEmail,
            "password": this.inputPassword,
            "birthday": this.inputBirthday,
            "date": this.inputDate,
            "time": this.inputTime,
            "gender": this.inputGender
        }

        let inputs = document.getElementsByTagName("input")
        for (let i=0; i < inputs.length; i++) {
            try {
                let input = inputs[i];
                let validateData = JSON.parse(input.getAttribute("validate").replaceAll("'", "\""));
                let validate = validateData['validate'];
                input.oninput = (v, func=validateFunc[validate], validateDatum=validateData) => {
                    if (func != null) func(validateDatum);
                }
            } catch (e) {}
        }
    }

    clearError(key) {
        let element = document.getElementById(key.trim()+"-error");
        if (element != null) {
            element.innerText = "";
        }
    }

    promptError(e) {
        let error = e.split(":")
        let error_key = error[1].trim();
        let error_message = error[2].trim();
        console.log(error_key.trim()+"-error");
        let element = document.getElementById(error_key.trim()+"-error");
        if (element != null) {
            element.innerText = error_message;
        }
    }

    number(num="0", key="number", call = "Number", float = true, required = true) {
        this.clearError(key);
        if (!required && num === "") {
            return "";
        }
        if (num === "") {
            throw new Error(`${key} : ${call} is required.`);
        }
        const regEx = float ? /^[0-9.]+$/ : /^[0-9]+$/;
        if (!regEx.test(num)) {
            throw new Error(`${key} : ${call} should be a number.`);
        }
        return num;
    }

    name(name="", key="name", call = "Name", spaces = true, unicode = false, minLength = 2, required = true) {
        this.clearError(key);
        if (!required && name === "") {
            return "";
        }
        if (name === "") {
            throw new Error(`${key} : ${call} is required.`);
        }
        if (!unicode && spaces && !/^[a-zA-Z\s]+$/.test(name)) {
            throw new Error(`${key} : ${call} should contain only letters and spaces.`);
        }
        if (!unicode && !spaces && !/^[a-zA-Z]+$/.test(name)) {
            throw new Error(`${key} : ${call} should contain only letters.`);
        }
        if (name.length < minLength) {
            throw new Error(`${key} : ${call} should have a minimum length of ${minLength} characters.`);
        }
        return name;
    }

    gmail(email="", key="email", call = "Email Address", required = true) {
        this.clearError(key);
        if (!required && email === "") {
            return "";
        }
        if (email === "") {
            throw new Error(`${key} : ${call} is required.`);
        }
        const regex = /^[a-z0-9._%+-]+@gmail\.com$/;
        if (!regex.test(email)) {
            throw new Error(`${key} : ${call} must end with @gmail.com`);
        }
        return email;
    }

    email(email="", key="email", call = "Email Address", required = true) {
        this.clearError(key);
        if (!required && email === "") {
            return "";
        }
        if (email === "") {
            throw new Error(`${key} : ${call} is required.`);
        }
        const regex = /^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}(?:\.[a-z]{2,})?$/;
        if (!regex.test(email)) {
            throw new Error(`${key} : ${call} is an invalid email address`);
        }
        return email;
    }

    password(password="", key="", call = "Password", required = true) {
        this.clearError(key);
        if (!required && password === "") {
            return "";
        }
        if (password === "") {
            throw new Error(`${key} : ${call} is required.`);
        }
        const minLength = 8;
        const maxLength = 20;
        const hasUppercase = /[A-Z]/.test(password);
        const hasLowercase = /[a-z]/.test(password);
        const hasNumber = /\d/.test(password);
        const hasSpecialChar = /[!@#$%^&*()\-_=+{}[\]|;:'",.<>/?~]/.test(password);

        if (password.length < minLength || password.length > maxLength) {
            throw new Error(`${key} : ${call} should have a length between ${minLength} and ${maxLength} characters.`);
        }
        if (!hasUppercase || !hasLowercase || !hasNumber || !hasSpecialChar) {
            throw new Error(`${key} : ${call} should meet the required criteria: at least one uppercase letter, one lowercase letter, one digit, and one special character.`);
        }
        return password;
    }

    birthday(birthday="", key="dob", call="Birthday", required = true) {
        this.clearError(key);
        if (!required && birthday === "") {
            return "";
        }
        if (birthday === "") {
            throw new Error(`${key} : ${call} is required.`);
        }
        if (!/^\d{4}-\d{2}-\d{2}$/.test(birthday)) {
            throw new Error(`${key} : ${call} is invalid.`);
        }
        const [year, month, day] = birthday.split('-');
        if (!this.isValidDate(year, month, day)) {
            throw new Error(`${key} : ${call} is invalid.`);
        }
        const today = new Date().toISOString().slice(0, 10);
        if (birthday >= today) {
            throw new Error(`${key} : ${call} is invalid.`);
        }
        return birthday;
    }

    isValidDate(year, month, day) {
        const date = new Date(year, month - 1, day);
        return (
            date.getFullYear() === year &&
            date.getMonth() + 1 === month &&
            date.getDate() === day
        );
    }

    date(date, key, call, greater = null, equal = false, required = true) {
        this.clearError(key);
        if (!required && date === "") {
            return "";
        }
        if (date === "") {
            throw new Error(`${key} : ${call} is required.`);
        }
        if (!/^\d{4}-\d{2}-\d{2}$/.test(date)) {
            throw new Error(`${key} : ${call} is invalid.`);
        }
        const [year, month, day] = date.split('-');
        if (!this.isValidDate(year, month, day)) {
            throw new Error(`${key} : ${call} is invalid.`);
        }
        const today = new Date().toISOString().slice(0, 10);

        if (greater === null && equal && date !== today) {
            throw new Error(`${key} : ${call} is invalid.`);
        } else if (greater && equal && date < today) {
            throw new Error(`${key} : ${call} is invalid.`);
        } else if (greater && !equal && date <= today) {
            throw new Error(`${key} : ${call} is invalid.`);
        } else if (equal && greater === null && date !== today) {
            throw new Error(`${key} : ${call} is invalid.`);
        } else if (equal && !greater && date > today) {
            throw new Error(`${key} : ${call} is invalid.`);
        } else if (!equal && !greater && date >= today) {
            throw new Error(`${key} : ${call} is invalid.`);
        }

        return date;
    }

    time(time="", key="", call, required = true) {
        this.clearError(key);
        if (!required && time === "") {
            return "";
        }
        if (time === "") {
            throw new Error(`${key} : ${call} is required.`);
        }
        if (!/^([01]\d|2[0-3]):([0-5]\d):([0-5]\d)$/.test(time)) {
            throw new Error(`${key} : ${call} is invalid.`);
        }
        return time;
    }

    gender(gender="", key="gender", call="Gender", required=true) {
        this.clearError(key);
        if (!required && gender === "") {
            return "";
        }
        if (isNaN(gender)) {
            throw new Error(`${key} : ${call} is invalid.`);
        }
        if (gender === "") {
            throw new Error(`${key} : ${call} is required.`);
        }
        gender = parseInt(gender);
        if (gender !== 1 && gender !== 2) {
            throw new Error(`${key} : ${call} is invalid.`);
        }
        return gender;
    }

    inputNumber(validateData) {
        try {
            let element = document.getElementById(validateData['name']);
            if (element != null && name != null) {
                VALIDATE.number(element.value, validateData['name'], validateData['call'], validateData['spaces']??true, validateData['unicode']??true, validateData['minLength']??true, validateData['required']);
            }
        } catch (e) {
            VALIDATE.promptError(e.toString());
        }
    }

    inputName(validateData) {
        try {
            let element = document.getElementById(validateData['name']);
            if (element != null && name != null) {
                VALIDATE.name(element.value, validateData['name'], validateData['call'], validateData['required']);
            }
        } catch (e) {
            VALIDATE.promptError(e.toString());
        }
    }

    inputGmail(validateData) {
        try {
            let element = document.getElementById(validateData['name']);
            if (element != null && name != null) {
                VALIDATE.gmail(element.value, validateData['name'], validateData['call'], validateData['required']);
            }
        } catch (e) {
            VALIDATE.promptError(e.toString());
        }
    }

    inputEmail(validateData) {
        try {
            let element = document.getElementById(validateData['name']);
            if (element != null && name != null) {
                VALIDATE.email(element.value, validateData['name'], validateData['call'], validateData['required']);
            }
        } catch (e) {
            VALIDATE.promptError(e.toString());
        }
    }

    inputPassword(validateData) {
        try {
            let element = document.getElementById(validateData['name']);
            if (element != null && name != null) {
                VALIDATE.password(element.value, validateData['name'], validateData['call'], validateData['required']);
            }
        } catch (e) {
            VALIDATE.promptError(e.toString());
        }
    }

    inputBirthday(validateData) {
        try {
            let element = document.getElementById(validateData['name']);
            if (element != null && name != null) {
                VALIDATE.birthday(element.value, validateData['name'], validateData['call'], validateData['required']);
            }
        } catch (e) {
            VALIDATE.promptError(e.toString());
        }
    }

    inputDate(validateData) {
        try {
            let element = document.getElementById(validateData['name']);
            if (element != null && name != null) {
                VALIDATE.date(element.value, validateData['name'], validateData['call'], validateData['greater'], validateData['equal'], validateData['required']);
            }
        } catch (e) {
            VALIDATE.promptError(e.toString());
        }
    }

    inputTime(validateData) {
        try {
            let element = document.getElementById(validateData['name']);
            if (element != null && name != null) {
                VALIDATE.time(element.value, validateData['name'], validateData['call'], validateData['required']);
            }
        } catch (e) {
            VALIDATE.promptError(e.toString());
        }
    }

    inputGender(validateData) {
        try {
            let element = document.getElementById(validateData['name']);
            if (element != null && name != null) {
                VALIDATE.gender(element.value, validateData['name'], validateData['call'], validateData['required']);
            }
        } catch (e) {
            VALIDATE.promptError(e.toString());
        }
    }
}
