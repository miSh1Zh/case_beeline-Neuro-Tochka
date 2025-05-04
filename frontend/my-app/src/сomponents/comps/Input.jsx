
import React, {useState} from "react";
import { css } from "../../styles/form.css";

// const object = {
//     one: 20,
//     two: 30,
//     three: 40
// }

// function example(object) {
//     const {one, two, three} = object;
//     return one + two + three;
// }



export const InputComponent = (props) => {

    const {placeholder, maxLength, action, inputValue} = props;

    // const [inputValue, setInputValue] = useState(0) //Без пропсов 

    return(
        <>
            <css.Input 
            value={inputValue}
            type={"text"} 
            placeholder={placeholder} 
            maxLength={maxLength}
            onChange={event => {
                const newValue = event.target.value
                action(newValue)
            }}
            />
            {/* <span style={{marginTop: "10px", marginBottom: "10px"}}>{inputValue} руб.</span> */}
        </>
    )
}