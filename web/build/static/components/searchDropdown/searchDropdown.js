import { LitElement, html, ref, createRef } from '/static/includes/open-wc/lit/lit-all.min.js';

import searchDropdownCSS from './searchDropdown.css' assert { type: 'css' }; 
import bootstrapIcon from '/static/includes/bootstrap-icons/bootstrap-icons.css' assert { type: 'css' }; 

class SearchDropdown extends LitElement {
    static styles = [ searchDropdownCSS, bootstrapIcon ]
    static get properties() {
        return {
            freetext: { type: Boolean },
            showing: { type: Boolean },
            value: { type: String },
            label: { type: String },
            text: { type: String, attribute: false },
            search: { type: String, attribute: false }
        }
    }
    inputRef = createRef();

    constructor() {
        super();
        this.showing = false;
        this.search = "";
        this.label = "Search";
        this.searchResults = 0;
        this.freetext = false;
        
        // Detect clicks not within the element to hide dropdown
        document.addEventListener("click", (e) => {
            if ( e.target != this ) {
                this.showing = false;
            }
        });
        window.addEventListener("blur", (e) => {
            if ( e.target != this ) {
                this.showing = false;
            }
        });
    }

    // Added hover title text to items and set text default to value
    firstUpdated() {
        super.firstUpdated();
        this.text = this.value;
        const childNodes = this.shadowRoot.querySelector('slot').assignedNodes();
        childNodes.map((node) => {
            if (node.text != undefined) {
                node.title = node.text;
            }
        })
        this.title = this.text;
    }
    // Detect showing change and auto focus search
    updated(changedProperties) {
        if (changedProperties.has("showing")) {
            if ( this.showing ) {
                this.inputRef.value.focus();
                this.shadowRoot.querySelector('.dropdownItemContainer').scrollTop = 0;
            } else {
                // Reset search and trigger a doSearch input event so all results are displayed
                this.inputRef.value.value = "";
                this.inputRef.value.dispatchEvent(new Event("input"));
            }
        } 
    }

    doSearch(e) {
        this.search = e.target.value;

        const childNodes = this.shadowRoot.querySelector('slot').assignedNodes();
        let resultCount = 0;
        childNodes.map((node) => {
            if (node.text != undefined) {
                if ( node.text.toLowerCase().includes(e.target.value.toLowerCase()) ) {
                    node.style.display = null;
                    resultCount+=1;
                } else {
                    node.style.display = "none";
                }
            }
        })
        this.searchResults = resultCount;
    }
    
    // Set the value and close the dropdown
    setValue(e) {
        this.text = e.target.text;
        this.value = e.target.value;
        this.showing = false;
        this.title = e.target.text;
        const childNodes = this.shadowRoot.querySelector('slot').assignedNodes();
        childNodes.map((node) => {
            if (node.text != undefined) {
                if (node.value == this.value) {
                    node.classList.add('highlighted');
                } else {
                    node.classList.remove('highlighted');
                }
            }
        })
        this.dispatchEvent(new CustomEvent('change', { bubbles: true, composed: true, target: { value: this.value } }));
    }

    setValueOnSubmit(e) {
        if (e.key == "Enter" && this.searchResults == 1) {
            const childNodes = this.shadowRoot.querySelector('slot').assignedNodes();
            childNodes.map((node) => {
                if (node.text != undefined) {
                    if (node.style.display != "none") {
                        this.setValue({ target: node })
                    }
                }
            })
        }
    }

    render() {
        return html`
            <div class="searchDropdown">
                <div class="searchDropdown-header" @click=${ () => this.showing = !this.showing }>
                    <a href="#" disabled>${this.text}</a> <span class="selectOpenClose bi-caret-${this.showing? "up" : "down"}"></span>
                </div>
                <div class="dropdownPanel" ?hidden=${!this.showing}>
                    <input type="text" placeholder=${this.label} ${ref(this.inputRef)} @input=${this.doSearch} @keypress=${this.setValueOnSubmit}/>
                    <div class="dropdownItemContainer">
                        <slot @click=${this.setValue}></slot>
                        ${this.freetext && this.search != "" && this.searchResults == 0 ? html`
                            <option title="${this.search}" @click=${this.setValue}>${this.search}</option>
                        ` : ""}
                    </div>
                </div>
            </div>
        `;
    }
}

customElements.define("search-dropdown", SearchDropdown);
